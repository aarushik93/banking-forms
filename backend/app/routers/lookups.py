from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from app import schemas
from app.adapters.address import AddressLookupProvider
from app.providers import get_address_provider
from app.services.bsb import get_bsb_service, normalise_bsb

router = APIRouter(prefix="/lookups", tags=["lookups"])


@router.get("/bsb/{bsb}", response_model=schemas.BsbLookupOut)
def lookup_bsb(bsb: str) -> schemas.BsbLookupOut:
    digits = normalise_bsb(bsb)
    if len(digits) != 6:
        raise HTTPException(status_code=422, detail="A BSB is 6 digits")
    service = get_bsb_service()
    entry = service.lookup(digits)
    if entry is None:
        return schemas.BsbLookupOut(
            bsb=digits, found=False, directory_available=service.available
        )
    return schemas.BsbLookupOut(
        bsb=digits,
        found=True,
        directory_available=True,
        bank_name=entry.bank_name,
        branch=entry.branch,
        suburb=entry.suburb,
        state=entry.state,
    )


@router.get("/address", response_model=list[schemas.AddressSuggestionOut])
def suggest_address(
    provider: Annotated[AddressLookupProvider, Depends(get_address_provider)],
    q: Annotated[str, Query(min_length=4, max_length=120)],
) -> list[schemas.AddressSuggestionOut]:
    return [
        schemas.AddressSuggestionOut(
            full_text=s.full_text,
            line1=s.line1,
            suburb=s.suburb,
            state=s.state,
            postcode=s.postcode,
        )
        for s in provider.search(q)
    ]
