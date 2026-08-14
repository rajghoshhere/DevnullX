from pathlib import Path
from uuid import uuid4

import httpx
import pytest

from adapters.storage.memory import InMemoryObjectStorage
from adapters.vehicle_providers.api_setu import (
    ApiSetuClientConfig,
    ApiSetuParseError,
    ApiSetuVehicleVerificationProvider,
    parse_api_setu_xml,
)
from domain.verification.types import VehicleVerificationResult, VerificationContext

FIXTURES = Path(__file__).parent / "fixtures"
SAMPLE_RC_XML = (FIXTURES / "sample_rc.xml").read_text(encoding="utf-8")

ERROR_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<VehicleDetails>
  <stautsMessage>ERROR</stautsMessage>
  <error_code>RECORD_NOT_FOUND</error_code>
</VehicleDetails>
"""

INCOMPLETE_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<VehicleDetails>
  <stautsMessage>OK</stautsMessage>
  <rc_maker_desc>TATA MOTORS LTD</rc_maker_desc>
</VehicleDetails>
"""

EXPECTED_RC_FIELDS = {
    "rc_regn_no": "MH12AB1234",
    "rc_maker_desc": "TATA MOTORS LTD",
    "rc_maker_model": "SIGNA 4825.T",
    "rc_body_type_desc": "TRUCK (OPEN BODY)",
    "rc_fuel_desc": "DIESEL",
    "rc_unld_wt": "12500",
    "rc_gvw": "47500",
    "rc_no_cyl": "6",
    "rc_cubic_cap": "6700.00",
    "rc_manu_month_yr": "01/2022",
}


def _context(registration: str = "MH12AB1234") -> VerificationContext:
    return VerificationContext(
        tenant_id=uuid4(),
        vehicle_id=uuid4(),
        correlation_id="corr-api-setu-1",
        registration_number=registration,
    )


def _config(
    *,
    base_url: str = "https://apisetu.example.test/vahan/rc",
    api_key: str = "test-api-key",
    client_id: str = "test-client-id",
    timeout_seconds: float = 0.5,
    max_attempts: int = 3,
    backoff_seconds: float = 0,
) -> ApiSetuClientConfig:
    return ApiSetuClientConfig(
        base_url=base_url,
        api_key=api_key,
        client_id=client_id,
        timeout_seconds=timeout_seconds,
        max_attempts=max_attempts,
        backoff_seconds=backoff_seconds,
    )


def _provider(
    transport: httpx.BaseTransport,
    storage: InMemoryObjectStorage | None = None,
    **config_overrides: object,
) -> tuple[ApiSetuVehicleVerificationProvider, InMemoryObjectStorage]:
    storage = storage or InMemoryObjectStorage()
    client = httpx.AsyncClient(transport=transport)
    provider = ApiSetuVehicleVerificationProvider(
        config=_config(**config_overrides),
        storage=storage,
        client=client,
    )
    return provider, storage


def test_parse_sample_xml_extracts_rc_fields() -> None:
    fields = parse_api_setu_xml(SAMPLE_RC_XML)
    for key, value in EXPECTED_RC_FIELDS.items():
        assert fields[key] == value
    assert fields["stautsMessage"] == "OK"
    assert fields["rc_regn_dt"] == "15-Mar-2022"
    assert fields["rc_vh_class_desc"] == "Goods Carrier(HGV)"
    assert fields["rc_status"] == "ACTIVE"
    assert "rc_chasi_no" in fields
    assert "rc_eng_no" in fields


def test_parse_rejects_invalid_xml() -> None:
    with pytest.raises(ApiSetuParseError):
        parse_api_setu_xml("<not-closed>")


async def test_successful_lookup_stores_raw_xml_and_returns_generic_result() -> None:
    captured: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        return httpx.Response(200, text=SAMPLE_RC_XML)

    provider, storage = _provider(httpx.MockTransport(handler))
    context = _context()
    result = await provider.verify_registration("MH12AB1234", context)

    assert result == VehicleVerificationResult(
        success=True,
        provider="api_setu",
        correlation_id="corr-api-setu-1",
        raw_object_key=(
            f"tenants/{context.tenant_id}/vehicles/{context.vehicle_id}"
            "/verification/corr-api-setu-1.xml"
        ),
        error_code=None,
    )
    assert not hasattr(result, "rc_regn_no")
    assert not hasattr(result, "rc_maker_desc")
    stored = await storage.get_bytes(result.raw_object_key or "")
    assert b"<rc_gvw>47500</rc_gvw>" in stored
    assert b"<rc_unld_wt>12500</rc_unld_wt>" in stored

    request = captured[0]
    assert request.method == "POST"
    assert str(request.url) == "https://apisetu.example.test/vahan/rc"
    assert request.headers["X-APISETU-APIKEY"] == "test-api-key"
    assert request.headers["X-APISETU-CLIENTID"] == "test-client-id"
    assert request.headers["X-Correlation-ID"] == "corr-api-setu-1"
    assert b"<rc_regn_no>MH12AB1234</rc_regn_no>" in request.content


async def test_provider_error_xml_is_stored_and_mapped() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=ERROR_XML)

    provider, storage = _provider(httpx.MockTransport(handler))
    result = await provider.verify_registration("MH12AB0000", _context())
    assert result.success is False
    assert result.error_code == "API_SETU_PROVIDER_ERROR"
    assert result.raw_object_key is not None
    assert b"RECORD_NOT_FOUND" in await storage.get_bytes(result.raw_object_key)


async def test_incomplete_xml_is_a_verification_failure() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=INCOMPLETE_XML)

    provider, _storage = _provider(httpx.MockTransport(handler))
    result = await provider.verify_registration("MH12AB1234", _context())
    assert result.success is False
    assert result.error_code == "API_SETU_INCOMPLETE_RESPONSE"


async def test_invalid_xml_body_is_stored() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="not-xml")

    provider, storage = _provider(httpx.MockTransport(handler))
    result = await provider.verify_registration("MH12AB1234", _context())
    assert result.success is False
    assert result.error_code == "API_SETU_INVALID_RESPONSE"
    assert await storage.get_bytes(result.raw_object_key or "") == b"not-xml"


@pytest.mark.parametrize(
    ("status_code", "error_code"),
    [
        (401, "API_SETU_UNAUTHORIZED"),
        (403, "API_SETU_UNAUTHORIZED"),
        (404, "API_SETU_NOT_FOUND"),
    ],
)
async def test_http_client_errors(status_code: int, error_code: str) -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code, text="<error/>")

    provider, _storage = _provider(
        httpx.MockTransport(handler),
        max_attempts=1,
    )
    result = await provider.verify_registration("MH12AB1234", _context())
    assert result.success is False
    assert result.error_code == error_code


async def test_retries_then_succeeds_on_service_unavailable() -> None:
    attempts = {"count": 0}

    def handler(_request: httpx.Request) -> httpx.Response:
        attempts["count"] += 1
        if attempts["count"] < 3:
            return httpx.Response(503, text="unavailable")
        return httpx.Response(200, text=SAMPLE_RC_XML)

    provider, _storage = _provider(httpx.MockTransport(handler), backoff_seconds=0)
    result = await provider.verify_registration("MH12AB1234", _context())
    assert attempts["count"] == 3
    assert result.success is True
    assert result.provider == "api_setu"


async def test_exhausted_retries_map_to_unavailable() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, text="unavailable")

    provider, storage = _provider(
        httpx.MockTransport(handler),
        max_attempts=2,
        backoff_seconds=0,
    )
    result = await provider.verify_registration("MH12AB1234", _context())
    assert result.success is False
    assert result.error_code == "API_SETU_UNAVAILABLE"
    assert result.raw_object_key is not None
    assert await storage.get_bytes(result.raw_object_key) == b"unavailable"


async def test_timeout_maps_to_timeout_error() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        raise httpx.TimeoutException("timed out")

    provider, storage = _provider(
        httpx.MockTransport(handler),
        max_attempts=2,
        backoff_seconds=0,
    )
    result = await provider.verify_registration("MH12AB1234", _context())
    assert result.success is False
    assert result.error_code == "API_SETU_TIMEOUT"
    assert result.raw_object_key is None
    assert storage.objects == {}


async def test_rate_limit_after_retries() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, text="slow down")

    provider, _storage = _provider(
        httpx.MockTransport(handler),
        max_attempts=2,
        backoff_seconds=0,
    )
    result = await provider.verify_registration("MH12AB1234", _context())
    assert result.success is False
    assert result.error_code == "API_SETU_RATE_LIMITED"


def test_config_rejects_missing_credentials() -> None:
    storage = InMemoryObjectStorage()
    with pytest.raises(ValueError, match="base URL"):
        ApiSetuVehicleVerificationProvider(
            config=_config(base_url=""),
            storage=storage,
        )
    with pytest.raises(ValueError, match="API key"):
        ApiSetuVehicleVerificationProvider(
            config=_config(api_key=""),
            storage=storage,
        )
