from __future__ import annotations

from typing import Protocol

from domain.verification.types import VehicleVerificationResult, VerificationContext


class VehicleVerificationProvider(Protocol):
    async def verify_registration(
        self,
        registration_number: str,
        context: VerificationContext,
    ) -> VehicleVerificationResult: ...
