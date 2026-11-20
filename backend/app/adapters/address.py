"""Live address autocomplete providers.

Autocomplete is a UX/data-quality aid — manual entry always remains
possible, and the KYC provider independently verifies the address — so
every provider here degrades to an empty suggestion list on failure
rather than blocking the applicant.

Providers:
- `NominatimAddressProvider` (default): OpenStreetMap's public geocoder,
  keyless. Fine for development and demos; its usage policy (1 req/s,
  attribution, no heavy production traffic) makes it unsuitable for a
  production bank — swap to Geoscape before go-live.
- `GeoscapeAddressProvider`: Geoscape Predictive Address API over the
  authoritative G-NAF dataset; needs an API key from geoscape.com.au.
  Confirm the request/response mapping against their current docs when
  onboarding.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Protocol

import httpx
import structlog

log = structlog.get_logger("address")

AU_STATES = {"NSW", "VIC", "QLD", "SA", "WA", "TAS", "ACT", "NT"}

STATE_ABBREVIATIONS = {
    "new south wales": "NSW",
    "victoria": "VIC",
    "queensland": "QLD",
    "south australia": "SA",
    "western australia": "WA",
    "tasmania": "TAS",
    "australian capital territory": "ACT",
    "northern territory": "NT",
}


@dataclass(frozen=True)
class AddressSuggestion:
    full_text: str
    line1: str
    suburb: str
    state: str
    postcode: str


class AddressLookupProvider(Protocol):
    def search(self, query: str, limit: int = 6) -> list[AddressSuggestion]: ...


class DisabledAddressProvider:
    def search(self, query: str, limit: int = 6) -> list[AddressSuggestion]:
        return []


class NominatimAddressProvider:
    def __init__(
        self,
        *,
        base_url: str = "https://nominatim.openstreetmap.org",
        client: httpx.Client | None = None,
    ) -> None:
        self._client = client or httpx.Client(
            base_url=base_url,
            timeout=5.0,
            headers={"User-Agent": "banking-forms/1.0 (managed funds application)"},
        )
        # Tiny TTL-less cache keeps repeat keystroke queries off the public API.
        self._cache: dict[str, list[AddressSuggestion]] = {}

    def search(self, query: str, limit: int = 6) -> list[AddressSuggestion]:
        key = query.strip().lower()
        if key in self._cache:
            return self._cache[key][:limit]
        try:
            response = self._client.get(
                "/search",
                params={
                    "q": query,
                    "countrycodes": "au",
                    "format": "jsonv2",
                    "addressdetails": 1,
                    "limit": limit,
                },
            )
            response.raise_for_status()
            results = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            log.warning("address_lookup_failed", provider="nominatim", error=str(exc))
            return []
        suggestions = []
        for item in results:
            suggestion = self._to_suggestion(item)
            if suggestion:
                suggestions.append(suggestion)
        if len(self._cache) > 512:
            self._cache.clear()
        self._cache[key] = suggestions
        return suggestions[:limit]

    @staticmethod
    def _to_suggestion(item: dict) -> AddressSuggestion | None:
        address = item.get("address", {})
        road = address.get("road")
        postcode = address.get("postcode")
        state = STATE_ABBREVIATIONS.get(str(address.get("state", "")).lower())
        suburb = (
            address.get("suburb")
            or address.get("town")
            or address.get("city")
            or address.get("village")
        )
        if not (road and postcode and state and suburb):
            return None
        house = address.get("house_number", "")
        line1 = f"{house} {road}".strip()
        return AddressSuggestion(
            full_text=f"{line1}, {suburb} {state} {postcode}",
            line1=line1,
            suburb=str(suburb),
            state=state,
            postcode=str(postcode),
        )


class GeoscapeAddressProvider:
    """Geoscape Predictive Address API client (suggest endpoint)."""

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str = "https://api.psma.com.au",
        client: httpx.Client | None = None,
    ) -> None:
        self._api_key = api_key
        self._client = client or httpx.Client(base_url=base_url, timeout=5.0)

    def search(self, query: str, limit: int = 6) -> list[AddressSuggestion]:
        try:
            response = self._client.get(
                "/v1/predictive/address",
                params={"query": query},
                headers={"Authorization": self._api_key},
            )
            response.raise_for_status()
            items = response.json().get("suggest", [])
        except (httpx.HTTPError, ValueError) as exc:
            log.warning("address_lookup_failed", provider="geoscape", error=str(exc))
            return []
        suggestions = []
        for item in items[:limit]:
            parsed = _parse_single_line(str(item.get("address", "")))
            if parsed:
                suggestions.append(parsed)
        return suggestions


def _parse_single_line(address: str) -> AddressSuggestion | None:
    """Parse 'UNIT 1 2 EXAMPLE ST, SUBURB NSW 2000' into components."""
    match = re.match(r"^(.*?),\s*(.+)\s+([A-Z]{2,3})\s+(\d{4})$", address.strip())
    if not match or match.group(3) not in AU_STATES:
        return None
    line1, suburb, state, postcode = match.groups()
    return AddressSuggestion(
        full_text=address.strip(),
        line1=line1.strip().title(),
        suburb=suburb.strip().title(),
        state=state,
        postcode=postcode,
    )
