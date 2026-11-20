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


# ---------------------------------------------------------------------------
# Generated personas: the scripted scenarios above stay canonical; the rest of
# the bureau is generated DETERMINISTICALLY (fixed seed) so every restart holds
# the same records. Browse them via GET /personas on the mock service.
# ---------------------------------------------------------------------------

import random
from datetime import date, timedelta

_FIRST_NAMES = (
    "James", "Olivia", "Liam", "Mia", "Ethan", "Ava", "Lucas", "Zoe", "Henry",
    "Ruby", "Mason", "Chloe", "Leo", "Harper", "Alexander", "Evie", "Daniel",
    "Matilda", "Samuel", "Willow", "Thomas", "Ivy", "Max", "Isabelle", "Hugo",
    "Freya", "Archie", "Stella", "Nathan", "Hannah", "Minh", "Linh", "Wei",
    "Mei", "Raj", "Priya", "Arjun", "Ananya", "Yusuf", "Fatima", "Omar",
    "Layla", "Dimitra", "Nikos", "Giulia", "Marco", "Elena", "Stefan", "Ingrid",
    "Lars", "Keiko", "Hiroshi", "Sione", "Talia", "Kiri", "Manaia", "Bronte",
    "Lachlan", "Sienna", "Callum",
)

_LAST_NAMES = (
    "Harris", "Walker", "Robinson", "Baker", "King", "Scott", "Mitchell",
    "Carter", "Turner", "Phillips", "Campbell", "Evans", "Collins", "Bennett",
    "Murphy", "Bailey", "Cooper", "Richardson", "Cox", "Ward", "Tran", "Pham",
    "Le", "Hoang", "Wang", "Li", "Zhang", "Liu", "Singh", "Kaur", "Sharma",
    "Gupta", "Ali", "Hassan", "Ibrahim", "Khan", "Papadopoulos", "Georgiou",
    "Rossi", "Ferrari", "Romano", "Costa", "Silva", "Santos", "Kowalski",
    "Novak", "Andersen", "Johansson", "Tanaka", "Sato", "Fonoti", "Ngata",
    "Te Rangi", "Dubois", "Moreau", "Schmidt", "Weber", "Van Der Berg",
    "O'Sullivan", "McGregor", "MacDonald", "Fraser", "Byrne", "Gallagher",
)

_LOCALITIES = (
    ("2000", "Sydney", "NSW"), ("2010", "Surry Hills", "NSW"),
    ("2026", "Bondi", "NSW"), ("2060", "North Sydney", "NSW"),
    ("2089", "Neutral Bay", "NSW"), ("2150", "Parramatta", "NSW"),
    ("2217", "Kogarah", "NSW"), ("2300", "Newcastle", "NSW"),
    ("2500", "Wollongong", "NSW"), ("2600", "Canberra", "ACT"),
    ("2601", "Acton", "ACT"), ("3000", "Melbourne", "VIC"),
    ("3008", "Docklands", "VIC"), ("3039", "Moonee Ponds", "VIC"),
    ("3053", "Carlton", "VIC"), ("3121", "Richmond", "VIC"),
    ("3182", "St Kilda", "VIC"), ("3550", "Bendigo", "VIC"),
    ("4000", "Brisbane", "QLD"), ("4006", "Newstead", "QLD"),
    ("4217", "Surfers Paradise", "QLD"), ("4350", "Toowoomba", "QLD"),
    ("4870", "Cairns", "QLD"), ("5000", "Adelaide", "SA"),
    ("5006", "North Adelaide", "SA"), ("6000", "Perth", "WA"),
    ("6160", "Fremantle", "WA"), ("7000", "Hobart", "TAS"),
    ("7250", "Launceston", "TAS"), ("0800", "Darwin", "NT"),
)

_REFER_SCENARIOS = (
    ("Thin file: single-source match only",
     {"CREDIT_HEADER": VERIFIED, "ELECTORAL_ROLL": NOT_FOUND,
      "DVS_DRIVERS_LICENCE": NOT_FOUND}, "CLEAR"),
    ("Recently moved: address disagrees with bureau records",
     {"CREDIT_HEADER": MISMATCH, "ELECTORAL_ROLL": VERIFIED,
      "DVS_DRIVERS_LICENCE": NOT_CHECKED}, "CLEAR"),
    ("Name and DOB verified but no address history",
     {"CREDIT_HEADER": VERIFIED, "ELECTORAL_ROLL": NOT_FOUND,
      "DVS_DRIVERS_LICENCE": NOT_CHECKED}, "CLEAR"),
    ("Fully verified but PEP hit -> enhanced due diligence",
     {"CREDIT_HEADER": VERIFIED, "ELECTORAL_ROLL": VERIFIED,
      "DVS_DRIVERS_LICENCE": VERIFIED}, "PEP"),
    ("Possible name variation (maiden/married name)",
     {"CREDIT_HEADER": MISMATCH, "ELECTORAL_ROLL": MISMATCH,
      "DVS_DRIVERS_LICENCE": NOT_CHECKED}, "CLEAR"),
)

_REJECT_SCENARIOS = (
    ("Identity verified but sanctions list hit",
     {"CREDIT_HEADER": VERIFIED, "ELECTORAL_ROLL": VERIFIED,
      "DVS_PASSPORT": VERIFIED}, "SANCTIONS"),
    ("Deceased flag on the credit header",
     {"CREDIT_HEADER": "DECEASED_FLAG", "ELECTORAL_ROLL": NOT_FOUND,
      "DVS_DRIVERS_LICENCE": NOT_CHECKED}, "CLEAR"),
    ("Fraud alert registered against this identity",
     {"CREDIT_HEADER": "FRAUD_ALERT", "ELECTORAL_ROLL": MISMATCH,
      "DVS_DRIVERS_LICENCE": NOT_FOUND}, "CLEAR"),
)

_ACCEPT_SOURCES = (
    {"CREDIT_HEADER": VERIFIED, "ELECTORAL_ROLL": VERIFIED,
     "DVS_DRIVERS_LICENCE": VERIFIED},
    {"CREDIT_HEADER": VERIFIED, "ELECTORAL_ROLL": VERIFIED,
     "DVS_DRIVERS_LICENCE": NOT_CHECKED},
    {"CREDIT_HEADER": VERIFIED, "ELECTORAL_ROLL": NOT_CHECKED,
     "DVS_PASSPORT": VERIFIED},
)


def _generate(count: int, seed: int = 42) -> list[dict]:
    rng = random.Random(seed)
    taken = {(p["first_name"].lower(), p["last_name"].lower()) for p in PERSONAS}
    taken.update({("any", "refer"), ("any", "reject"), ("any", "fault")})
    generated: list[dict] = []
    while len(generated) < count:
        first = rng.choice(_FIRST_NAMES)
        last = rng.choice(_LAST_NAMES)
        if (first.lower(), last.lower()) in taken or last.upper() in {
            "REFER", "REJECT", "FAULT",
        }:
            continue
        taken.add((first.lower(), last.lower()))
        dob = date(1946, 1, 1) + timedelta(days=rng.randrange(0, 365 * 60))
        postcode, suburb, state = rng.choice(_LOCALITIES)
        roll = rng.random()
        if roll < 0.82:  # realistic eIDV pass rates sit around 80-90%
            scenario = "Clean electronic verification"
            sources = rng.choice(_ACCEPT_SOURCES)
            outcome, watchlist = "ACCEPT", "CLEAR"
            points = rng.randrange(280, 401)
        elif roll < 0.94:
            scenario, sources, watchlist = rng.choice(_REFER_SCENARIOS)
            outcome = "REFER"
            points = rng.randrange(280, 341) if watchlist == "PEP" else rng.randrange(100, 261)
        else:
            scenario, sources, watchlist = rng.choice(_REJECT_SCENARIOS)
            outcome = "REJECT"
            points = (
                rng.randrange(280, 341)
                if watchlist == "SANCTIONS"
                else rng.randrange(0, 121)
            )
        generated.append(
            {
                "first_name": first,
                "last_name": last,
                "date_of_birth": dob.isoformat(),
                "postcode": postcode,
                "suburb": suburb,
                "state": state,
                "outcome": outcome,
                "points": points,
                "watchlist": watchlist,
                "sources": sources,
                "scenario": scenario,
            }
        )
    return generated


_SCRIPTED_LOCALITIES = {
    "2000": ("Sydney", "NSW"),
    "3000": ("Melbourne", "VIC"),
    "4000": ("Brisbane", "QLD"),
    "5000": ("Adelaide", "SA"),
    "6000": ("Perth", "WA"),
    "2150": ("Parramatta", "NSW"),
    "3182": ("St Kilda", "VIC"),
    "2010": ("Surry Hills", "NSW"),
    "2300": ("Newcastle", "NSW"),
    "2600": ("Canberra", "ACT"),
}
for _p in PERSONAS:
    _suburb, _state = _SCRIPTED_LOCALITIES[_p["postcode"]]
    _p.setdefault("suburb", _suburb)
    _p.setdefault("state", _state)

ALL_PERSONAS: list[dict] = PERSONAS + _generate(190)


def find_persona(first_name: str, last_name: str) -> dict | None:
    first = first_name.strip().lower()
    last = last_name.strip().lower()
    for persona in ALL_PERSONAS:
        if persona["first_name"].lower() == first and persona["last_name"].lower() == last:
            return persona
    return None
