from uuid import uuid4

from adapters.vehicle_providers.fake import FakeVehicleVerificationProvider
from domain.verification.types import VerificationContext


def _context(registration: str) -> VerificationContext:
    return VerificationContext(
        tenant_id=uuid4(),
        vehicle_id=uuid4(),
        correlation_id="corr-1",
        registration_number=registration,
    )


async def test_fake_provider_succeeds_by_default() -> None:
    provider = FakeVehicleVerificationProvider()
    result = await provider.verify_registration("MH12AB1234", _context("MH12AB1234"))
    assert result.success is True
    assert result.provider == "fake"
    assert result.error_code is None
    assert result.attributes is not None
    assert result.attributes.gvw_kg == 47500
    assert result.attributes.fuel_type == "DIESEL"


async def test_fake_provider_fails_when_registration_contains_fail() -> None:
    provider = FakeVehicleVerificationProvider()
    result = await provider.verify_registration("MH12FAIL1", _context("MH12FAIL1"))
    assert result.success is False
    assert result.error_code == "FAKE_VERIFICATION_FAILED"


async def test_fake_provider_can_be_forced_to_fail() -> None:
    provider = FakeVehicleVerificationProvider(succeed=False)
    result = await provider.verify_registration("MH12AB1234", _context("MH12AB1234"))
    assert result.success is False
