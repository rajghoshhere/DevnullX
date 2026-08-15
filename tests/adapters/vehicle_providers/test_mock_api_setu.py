from uuid import uuid4

import httpx

from adapters.storage.memory import InMemoryObjectStorage
from adapters.vehicle_providers.api_setu import (
    ApiSetuClientConfig,
    ApiSetuVehicleVerificationProvider,
    parse_api_setu_xml,
)
from adapters.vehicle_providers.mock_api_setu import app
from domain.verification.types import VerificationContext


def _client() -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://mock")


def _context(registration: str = "MH12AB1234") -> VerificationContext:
    return VerificationContext(
        tenant_id=uuid4(),
        vehicle_id=uuid4(),
        correlation_id="corr-mock-1",
        registration_number=registration,
    )


async def test_mock_health() -> None:
    async with _client() as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "provider": "mock-api-setu"}


async def test_mock_returns_sample_rc_xml() -> None:
    async with _client() as client:
        response = await client.post(
            "/vahan/rc",
            content=b"<VehicleDetailsRequest><rc_regn_no>MH12AB1234</rc_regn_no></VehicleDetailsRequest>",
            headers={"X-APISETU-APIKEY": "test-api-key", "X-APISETU-CLIENTID": "test-client"},
        )
    assert response.status_code == 200
    fields = parse_api_setu_xml(response.text)
    assert fields["rc_regn_no"] == "MH12AB1234"
    assert fields["rc_gvw"] == "47500"
    assert fields["stautsMessage"] == "OK"


async def test_mock_rejects_missing_api_key() -> None:
    async with _client() as client:
        response = await client.post(
            "/vahan/rc",
            content=b"<VehicleDetailsRequest><rc_regn_no>MH12AB1234</rc_regn_no></VehicleDetailsRequest>",
        )
    assert response.status_code == 401


async def test_mock_returns_error_xml_for_fail_registration() -> None:
    async with _client() as client:
        response = await client.post(
            "/vahan/rc",
            content=b"<VehicleDetailsRequest><rc_regn_no>MH12FAIL99</rc_regn_no></VehicleDetailsRequest>",
            headers={"X-APISETU-APIKEY": "test-api-key"},
        )
    assert response.status_code == 200
    fields = parse_api_setu_xml(response.text)
    assert fields["stautsMessage"] == "ERROR"


async def test_api_setu_adapter_populates_from_mock() -> None:
    async with _client() as client:
        provider = ApiSetuVehicleVerificationProvider(
            config=ApiSetuClientConfig(
                base_url="http://mock/vahan/rc",
                api_key="test-api-key",
                client_id="test-client",
                max_attempts=1,
            ),
            storage=InMemoryObjectStorage(),
            client=client,
        )
        result = await provider.verify_registration("MH12AB1234", _context())
    assert result.success is True
    assert result.attributes is not None
    assert result.attributes.gvw_kg == 47500
    assert result.attributes.unladen_weight_kg == 12500
    assert result.attributes.fuel_type == "DIESEL"
    assert result.attributes.body_type == "OPEN"


async def test_api_setu_adapter_maps_mock_failure() -> None:
    async with _client() as client:
        provider = ApiSetuVehicleVerificationProvider(
            config=ApiSetuClientConfig(
                base_url="http://mock/vahan/rc",
                api_key="test-api-key",
                client_id="test-client",
                max_attempts=1,
            ),
            storage=InMemoryObjectStorage(),
            client=client,
        )
        result = await provider.verify_registration("KA01FAIL99", _context("KA01FAIL99"))
    assert result.success is False
    assert result.error_code == "API_SETU_PROVIDER_ERROR"
