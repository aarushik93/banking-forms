"""Dynamic BSB directory lookup.

Fetches AusPayNet's official full BSB directory from its permanent public
URL at runtime, indexes it in memory, and refreshes on a TTL (AusPayNet
publishes updates monthly; we refresh daily). No data ships with the app.
If the directory cannot be fetched, lookups report unavailable and the
submit-time check degrades gracefully instead of blocking applicants.
"""

from __future__ import annotations

import csv
import threading
import time
from dataclasses import dataclass

import httpx
import structlog

from app.config import get_settings

log = structlog.get_logger("bsb")

# Friendly names for common institution mnemonics in the AusPayNet file.
BANK_NAMES = {
    "ANZ": "ANZ",
    "CBA": "Commonwealth Bank",
    "NAB": "National Australia Bank",
    "WBC": "Westpac",
    "STG": "St George Bank",
    "BSA": "BankSA",
    "BOM": "Bank of Melbourne",
    "BOQ": "Bank of Queensland",
    "BEN": "Bendigo Bank",
    "SUN": "Suncorp Bank",
    "MBL": "Macquarie Bank",
    "ING": "ING",
    "AMP": "AMP Bank",
    "HSB": "HSBC",
    "HBA": "HSBC",
    "CTI": "Citibank",
    "BWA": "Bankwest",
    "MEB": "ME Bank",
    "UBL": "UBank",
    "GSB": "Great Southern Bank",
    "NPB": "Newcastle Permanent",
    "HER": "Heritage Bank",
    "ADL": "Adelaide Bank",
    "RAB": "Rabobank",
    "JUD": "Judo Bank",
}


def normalise_bsb(value: str) -> str:
    return "".join(c for c in value if c.isdigit())


@dataclass(frozen=True)
class BsbEntry:
    bsb: str  # 6 digits, no separator
    bank_code: str
    bank_name: str
    branch: str
    suburb: str
    state: str


class BsbDirectoryService:
    def __init__(
        self,
        *,
        url: str,
        refresh_seconds: int = 86400,
        client: httpx.Client | None = None,
    ) -> None:
        self._url = url
        self._refresh_seconds = refresh_seconds
        self._client = client or httpx.Client(timeout=30.0, follow_redirects=True)
        self._entries: dict[str, BsbEntry] | None = None
        self._loaded_at = 0.0
        self._lock = threading.Lock()

    @property
    def available(self) -> bool:
        return self._entries is not None

    def entry_count(self) -> int:
        return len(self._entries) if self._entries else 0

    def _parse(self, text: str) -> dict[str, BsbEntry]:
        entries: dict[str, BsbEntry] = {}
        for row in csv.reader(text.splitlines()):
            if len(row) < 7:
                continue
            bsb = normalise_bsb(row[0])
            if len(bsb) != 6:
                continue
            mnemonic = row[1].strip()
            entries[bsb] = BsbEntry(
                bsb=bsb,
                bank_code=mnemonic,
                bank_name=BANK_NAMES.get(mnemonic, mnemonic),
                branch=row[2].strip(),
                suburb=row[4].strip(),
                state=row[5].strip(),
            )
        return entries

    def refresh(self, force: bool = False) -> None:
        with self._lock:
            fresh = (
                self._entries is not None
                and time.monotonic() - self._loaded_at < self._refresh_seconds
            )
            if fresh and not force:
                return
            try:
                response = self._client.get(self._url)
                response.raise_for_status()
                entries = self._parse(response.text)
                if not entries:
                    raise ValueError("directory parsed to zero entries")
                self._entries = entries
                self._loaded_at = time.monotonic()
                log.info("bsb_directory_refreshed", entries=len(entries), source=self._url)
            except Exception as exc:
                # Keep serving the previous copy (if any); never crash a request.
                log.warning("bsb_directory_refresh_failed", error=str(exc))
                self._loaded_at = time.monotonic()  # back off until next TTL window

    def lookup(self, bsb: str) -> BsbEntry | None:
        self.refresh()
        if self._entries is None:
            return None
        return self._entries.get(normalise_bsb(bsb))


_service: BsbDirectoryService | None = None


def get_bsb_service() -> BsbDirectoryService:
    global _service
    if _service is None:
        settings = get_settings()
        _service = BsbDirectoryService(
            url=settings.bsb_directory_url,
            refresh_seconds=settings.bsb_refresh_seconds,
        )
    return _service
