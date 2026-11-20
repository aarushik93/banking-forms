"""Seeded test personas for the mock IDMatrix bureau.

Modeled on how real IDV sandboxes work: the bureau holds records, and the
outcome depends on how well the submitted identity matches them. Each persona
scripts a realistic verification scenario. All identities are fictional.

Matching rules (see server.py):
- first + last name match a persona  -> that persona's scenario applies,
  but a wrong DOB or postcode downgrades it to a partial-match REFER
  (exactly what a real bureau does with inconsistent data)
- no persona match                   -> surname triggers (Refer/Reject/Fault)
  still work, otherwise MOCK_DEFAULT_OUTCOME applies (ACCEPT by default for
  demo friendliness; set REFER for realistic "unknown identity" behaviour)
"""

VERIFIED = "VERIFIED"
NOT_FOUND = "NOT_FOUND"
MISMATCH = "MISMATCH"
NOT_CHECKED = "NOT_CHECKED"

PERSONAS = [
    {
        "first_name": "Charlotte",
        "last_name": "Anderson",
        "date_of_birth": "1988-03-15",
        "postcode": "2000",
        "outcome": "ACCEPT",
        "points": 340,
        "watchlist": "CLEAR",
        "sources": {
            "CREDIT_HEADER": VERIFIED,
            "ELECTORAL_ROLL": VERIFIED,
            "DVS_DRIVERS_LICENCE": VERIFIED,
        },
        "scenario": "Clean full match across three sources",
    },
    {
        "first_name": "Oliver",
        "last_name": "Nguyen",
        "date_of_birth": "1992-11-02",
        "postcode": "3000",
        "outcome": "ACCEPT",
        "points": 310,
        "watchlist": "CLEAR",
        "sources": {
            "CREDIT_HEADER": VERIFIED,
            "ELECTORAL_ROLL": NOT_CHECKED,
            "DVS_PASSPORT": VERIFIED,
        },
        "scenario": "Verified via credit header + passport (DVS)",
    },
    {
        "first_name": "Amelia",
        "last_name": "Patel",
        "date_of_birth": "1975-06-30",
        "postcode": "4000",
        "outcome": "ACCEPT",
        "points": 280,
        "watchlist": "CLEAR",
        "sources": {
            "CREDIT_HEADER": VERIFIED,
            "ELECTORAL_ROLL": VERIFIED,
            "DVS_DRIVERS_LICENCE": NOT_CHECKED,
        },
        "scenario": "Two-source match, exactly at the accept threshold",
    },
    {
        "first_name": "Jack",
        "last_name": "Thompson",
        "date_of_birth": "2001-09-12",
        "postcode": "5000",
        "outcome": "REFER",
        "points": 120,
        "watchlist": "CLEAR",
        "sources": {
            "CREDIT_HEADER": VERIFIED,
            "ELECTORAL_ROLL": NOT_FOUND,
            "DVS_DRIVERS_LICENCE": NOT_FOUND,
        },
        "scenario": "Thin file: young applicant, single-source match only",
    },
    {
        "first_name": "Isla",
        "last_name": "Fitzgerald",
        "date_of_birth": "1983-01-25",
        "postcode": "6000",
        "outcome": "REFER",
        "points": 180,
        "watchlist": "CLEAR",
        "sources": {
            "CREDIT_HEADER": MISMATCH,
            "ELECTORAL_ROLL": VERIFIED,
            "DVS_DRIVERS_LICENCE": NOT_CHECKED,
        },
        "scenario": "Recently moved: address disagrees with bureau records",
    },
    {
        "first_name": "William",
        "last_name": "Chen",
        "date_of_birth": "1990-05-05",
        "postcode": "2150",
        "outcome": "REFER",
        "points": 200,
        "watchlist": "CLEAR",
        "sources": {
            "CREDIT_HEADER": VERIFIED,
            "ELECTORAL_ROLL": NOT_FOUND,
            "DVS_DRIVERS_LICENCE": NOT_CHECKED,
        },
        "scenario": "Name and DOB verified but no address history",
    },
    {
        "first_name": "Sofia",
        "last_name": "Marino",
        "date_of_birth": "1979-04-19",
        "postcode": "3182",
        "outcome": "REFER",
        "points": 300,
        "watchlist": "PEP",
        "sources": {
            "CREDIT_HEADER": VERIFIED,
            "ELECTORAL_ROLL": VERIFIED,
            "DVS_DRIVERS_LICENCE": VERIFIED,
        },
        "scenario": "Fully verified but PEP hit -> enhanced due diligence",
    },
    {
        "first_name": "Dmitri",
        "last_name": "Volkov",
        "date_of_birth": "1970-12-01",
        "postcode": "2010",
        "outcome": "REJECT",
        "points": 290,
        "watchlist": "SANCTIONS",
        "sources": {
            "CREDIT_HEADER": VERIFIED,
            "ELECTORAL_ROLL": VERIFIED,
            "DVS_PASSPORT": VERIFIED,
        },
        "scenario": "Identity verified but sanctions list hit",
    },
    {
        "first_name": "Noah",
        "last_name": "Williams",
        "date_of_birth": "1958-07-08",
        "postcode": "2300",
        "outcome": "REJECT",
        "points": 0,
        "watchlist": "CLEAR",
        "sources": {
            "CREDIT_HEADER": "DECEASED_FLAG",
            "ELECTORAL_ROLL": NOT_FOUND,
            "DVS_DRIVERS_LICENCE": NOT_CHECKED,
        },
        "scenario": "Deceased flag on the credit header",
    },
    {
        "first_name": "Grace",
        "last_name": "O'Connor",
        "date_of_birth": "1995-08-22",
        "postcode": "2600",
        "outcome": "REJECT",
        "points": 60,
        "watchlist": "CLEAR",
        "sources": {
            "CREDIT_HEADER": "FRAUD_ALERT",
            "ELECTORAL_ROLL": MISMATCH,
            "DVS_DRIVERS_LICENCE": NOT_FOUND,
        },
        "scenario": "Fraud alert registered against this identity",
    },
]


def find_persona(first_name: str, last_name: str) -> dict | None:
    first = first_name.strip().lower()
    last = last_name.strip().lower()
    for persona in PERSONAS:
        if persona["first_name"].lower() == first and persona["last_name"].lower() == last:
            return persona
    return None
