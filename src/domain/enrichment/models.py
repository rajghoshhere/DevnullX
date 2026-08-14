from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from domain.tenant.entities import utc_now

SOURCE_DERIVED = "DERIVED"
SOURCE_SYSTEM_RULE_ENGINE = "RULE_ENGINE"


@dataclass(frozen=True, slots=True)
class Rule:
    rule_id: str
    name: str
    version: str
    rule_type: str
    expression: Mapping[str, Any]
    priority: int
    active: bool
    effective_from: datetime | None
    effective_to: datetime | None
    author: str | None
    created_at: datetime
    updated_at: datetime

    @staticmethod
    def create(
        *,
        rule_id: str,
        name: str,
        version: str,
        rule_type: str,
        expression: Mapping[str, Any],
        priority: int,
        active: bool = True,
        effective_from: datetime | None = None,
        effective_to: datetime | None = None,
        author: str | None = None,
    ) -> Rule:
        if not rule_id.strip():
            raise ValueError("rule_id is required")
        if not version.strip():
            raise ValueError("rule version is required")
        if not rule_type.strip():
            raise ValueError("rule_type is required")
        now = utc_now()
        return Rule(
            rule_id=rule_id.strip(),
            name=name.strip(),
            version=version.strip(),
            rule_type=rule_type.strip(),
            expression=dict(expression),
            priority=priority,
            active=active,
            effective_from=effective_from,
            effective_to=effective_to,
            author=author,
            created_at=now,
            updated_at=now,
        )

    def is_effective_at(self, moment: datetime) -> bool:
        if not self.active:
            return False
        if self.effective_from is not None and moment < self.effective_from:
            return False
        if self.effective_to is not None and moment >= self.effective_to:
            return False
        return True


@dataclass(frozen=True, slots=True)
class AttributeProvenance:
    attribute: str
    value: str
    source: str
    source_system: str
    source_field: str | None
    source_record_id: str | None
    transformation_type: str
    rule_id: str
    rule_version: str
    confidence: float
    timestamp: datetime


@dataclass(frozen=True, slots=True)
class RuleResult:
    rule_id: str
    rule_version: str
    attribute: str
    value: str | None
    applied: bool
    skipped_reason: str | None
    provenance: AttributeProvenance | None


@dataclass(frozen=True, slots=True)
class VehicleFacts:
    gvw_kg: int | None = None
    unladen_weight_kg: int | None = None
    raw_body_text: str | None = None
    raw_manufacturer: str | None = None
    known_attributes: dict[str, str] = field(default_factory=dict)

    def numeric(self, field_name: str) -> int | None:
        if field_name == "gvw_kg":
            return self.gvw_kg
        if field_name == "unladen_weight_kg":
            return self.unladen_weight_kg
        raise KeyError(field_name)

    def text(self, field_name: str) -> str | None:
        if field_name == "raw_body_text":
            return self.raw_body_text
        if field_name == "raw_manufacturer":
            return self.raw_manufacturer
        raise KeyError(field_name)


@dataclass(frozen=True, slots=True)
class VehicleAttributeProvenance:
    id: UUID
    tenant_id: UUID
    vehicle_id: UUID
    attribute: str
    value: str
    source: str
    source_system: str
    source_field: str | None
    source_record_id: str | None
    transformation_type: str
    rule_id: str
    rule_version: str
    confidence: float
    created_at: datetime

    @staticmethod
    def from_result(
        *,
        tenant_id: UUID,
        vehicle_id: UUID,
        result: RuleResult,
    ) -> VehicleAttributeProvenance:
        if result.provenance is None:
            raise ValueError("cannot persist provenance for a skipped rule")
        provenance = result.provenance
        return VehicleAttributeProvenance(
            id=uuid4(),
            tenant_id=tenant_id,
            vehicle_id=vehicle_id,
            attribute=provenance.attribute,
            value=provenance.value,
            source=provenance.source,
            source_system=provenance.source_system,
            source_field=provenance.source_field,
            source_record_id=provenance.source_record_id,
            transformation_type=provenance.transformation_type,
            rule_id=provenance.rule_id,
            rule_version=provenance.rule_version,
            confidence=provenance.confidence,
            created_at=provenance.timestamp,
        )
