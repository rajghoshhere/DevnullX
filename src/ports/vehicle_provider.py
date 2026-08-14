from __future__ import annotations

from typing import Protocol

from domain.verification.types import VerificationContext, VehicleVerificationResult


class VehicleVerificationProvider(Protocol):
    async def verify_registration(
        self,
        registration_number: str,
        context: VerificationContext,
    ) -> VehicleVerificationResult: ...
