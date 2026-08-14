from __future__ import annotations

from domain.verification.types import VehicleVerificationResult, VerificationContext


class FakeVehicleVerificationProvider:
    """In-process stand-in until an external vehicle API adapter exists."""

    def __init__(self, *, succeed: bool = True) -> None:
        self.succeed = succeed
        self.calls: list[tuple[str, VerificationContext]] = []

    async def verify_registration(
        self,
        registration_number: str,
        context: VerificationContext,
    ) -> VehicleVerificationResult:
        self.calls.append((registration_number, context))
        failed = (not self.succeed) or "FAIL" in registration_number.upper()
        return VehicleVerificationResult(
            success=not failed,
            provider="fake",
            correlation_id=context.correlation_id,
            raw_object_key=None,
            error_code="FAKE_VERIFICATION_FAILED" if failed else None,
        )
