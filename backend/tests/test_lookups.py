import httpx

from app.adapters.address import NominatimAddressProvider
from app.services.bsb import BsbDirectoryService

BSB_CSV = (
    '"062-000","CBA","48 Martin Place Sydney","48 Martin Place","Sydney","NSW","2000","PEH"\n'
    '"012-002","ANZ","ANZ Smart Choice","115 Pitt Street","Sydney","NSW","2000","PEH"\n'
)


def _bsb_service(handler) -> BsbDirectoryService:
    client = httpx.Client(transport=httpx.MockTransport(handler))
    return BsbDirectoryService(url="https://bsb.test/full.csv", client=client)


def test_bsb_service_fetches_and_indexes():
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(200, text=BSB_CSV)

    service = _bsb_service(handler)
    entry = service.lookup("062-000")
    assert entry is not None
    assert entry.bank_name == "Commonwealth Bank"
    assert entry.suburb == "Sydney"
    assert service.lookup("999999") is None
    assert service.entry_count() == 2
    # Directory is cached, not re-fetched per lookup
    service.lookup("012002")
    assert calls["n"] == 1


def test_bsb_service_degrades_when_unreachable():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("down")

    service = _bsb_service(handler)
    assert service.lookup("062000") is None
    assert service.available is False


def test_bsb_endpoint_validates_format(client):
    assert client.get("/api/v1/lookups/bsb/12").status_code == 422
    resp = client.get("/api/v1/lookups/bsb/062-000")
    assert resp.status_code == 200
    body = resp.json()
    # Directory URL is unroutable in tests, so lookups report unavailable
    assert body["found"] is False
    assert body["directory_available"] is False


NOMINATIM_RESULT = [
    {
        "display_name": "1, George Street, Sydney, NSW, 2000, Australia",
        "address": {
            "house_number": "1",
            "road": "George Street",
            "suburb": "Sydney",
            "state": "New South Wales",
            "postcode": "2000",
        },
    },
    {
        # Missing road/postcode entries are filtered out
        "display_name": "Sydney, Australia",
        "address": {"city": "Sydney", "state": "New South Wales"},
    },
]


def test_nominatim_provider_maps_results():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["countrycodes"] == "au"
        return httpx.Response(200, json=NOMINATIM_RESULT)

    client = httpx.Client(
        base_url="https://nominatim.test", transport=httpx.MockTransport(handler)
    )
    provider = NominatimAddressProvider(client=client)
    results = provider.search("1 george street sydney")
    assert len(results) == 1
    assert results[0].line1 == "1 George Street"
    assert results[0].state == "NSW"
    assert results[0].postcode == "2000"


def test_nominatim_provider_degrades_on_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503)

    client = httpx.Client(
        base_url="https://nominatim.test", transport=httpx.MockTransport(handler)
    )
    assert NominatimAddressProvider(client=client).search("1 george st") == []
