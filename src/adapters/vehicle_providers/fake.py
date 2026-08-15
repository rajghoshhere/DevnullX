from __future__ import annotations

from datetime import date

from domain.verification.types import (
    VehicleVerificationResult,
    VerificationContext,
    VerifiedVehicleAttributes,
)


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
            attributes=None if failed else _demo_attributes(),
        )


def _demo_attributes() -> VerifiedVehicleAttributes:
    return VerifiedVehicleAttributes(
        registration_date=date(2022, 3, 15),
        manufacturing_month_year=date(2022, 1, 1),
        gvw_kg=47500,
        unladen_weight_kg=12500,
        engine_cc=6700,
        cylinder_count=6,
        fuel_type="DIESEL",
        body_type="OPEN",
    )
