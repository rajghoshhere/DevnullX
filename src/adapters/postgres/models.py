from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from adapters.postgres.base import Base
from adapters.postgres.taxonomy_models import (
    AxleConfigurationModel,
    BodyTypeModel,
    PowertrainModel,
    RegulatoryCategoryModel,
    TruckApplicationModel,
    TruckConfigurationModel,
    TruckSegmentModel,
)
from domain.vehicle.states import VehicleStatus


class TenantModel(Base):
    __tablename__ = "tenants"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    fleet_owners: Mapped[list[FleetOwnerModel]] = relationship(back_populates="tenant")
    fleets: Mapped[list[FleetModel]] = relationship(back_populates="tenant")
    vehicles: Mapped[list[VehicleModel]] = relationship(back_populates="tenant")


class FleetOwnerModel(Base):
    __tablename__ = "fleet_owners"
    __table_args__ = (Index("ix_fleet_owners_tenant_id", "tenant_id"),)

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    tenant_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("tenants.id", ondelete="RESTRICT"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    tenant: Mapped[TenantModel] = relationship(back_populates="fleet_owners")


class FleetModel(Base):
    __tablename__ = "fleets"
    __table_args__ = (Index("ix_fleets_tenant_id", "tenant_id"),)

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    tenant_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("tenants.id", ondelete="RESTRICT"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    tenant: Mapped[TenantModel] = relationship(back_populates="fleets")
    vehicles: Mapped[list[VehicleModel]] = relationship(back_populates="fleet")


class ManufacturerModel(Base):
    __tablename__ = "manufacturers"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    truck_models: Mapped[list[TruckModelRecord]] = relationship(back_populates="manufacturer")


class TruckModelRecord(Base):
    __tablename__ = "truck_models"
    __table_args__ = (
        Index("ix_truck_models_manufacturer_id", "manufacturer_id"),
        Index("ix_truck_models_regulatory_category_id", "regulatory_category_id"),
        Index("ix_truck_models_truck_segment_id", "truck_segment_id"),
        Index("ix_truck_models_truck_configuration_id", "truck_configuration_id"),
        Index("ix_truck_models_body_type_id", "body_type_id"),
        Index("ix_truck_models_axle_configuration_id", "axle_configuration_id"),
        Index("ix_truck_models_powertrain_id", "powertrain_id"),
        Index("ix_truck_models_truck_application_id", "truck_application_id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    manufacturer_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("manufacturers.id", ondelete="RESTRICT"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    regulatory_category_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("regulatory_categories.id", ondelete="RESTRICT"),
        nullable=True,
    )
    truck_segment_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("truck_segments.id", ondelete="RESTRICT"),
        nullable=True,
    )
    truck_configuration_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("truck_configurations.id", ondelete="RESTRICT"),
        nullable=True,
    )
    body_type_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("body_types.id", ondelete="RESTRICT"),
        nullable=True,
    )
    axle_configuration_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("axle_configurations.id", ondelete="RESTRICT"),
        nullable=True,
    )
    powertrain_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("powertrains.id", ondelete="RESTRICT"),
        nullable=True,
    )
    truck_application_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("truck_applications.id", ondelete="RESTRICT"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    manufacturer: Mapped[ManufacturerModel] = relationship(back_populates="truck_models")
    vehicles: Mapped[list[VehicleModel]] = relationship(back_populates="truck_model")
    regulatory_category: Mapped[RegulatoryCategoryModel | None] = relationship()
    truck_segment: Mapped[TruckSegmentModel | None] = relationship()
    truck_configuration: Mapped[TruckConfigurationModel | None] = relationship()
    body_type: Mapped[BodyTypeModel | None] = relationship()
    axle_configuration: Mapped[AxleConfigurationModel | None] = relationship()
    powertrain: Mapped[PowertrainModel | None] = relationship()
    truck_application: Mapped[TruckApplicationModel | None] = relationship()


class VehicleModel(Base):
    __tablename__ = "vehicles"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "normalized_registration_number",
            name="uq_vehicles_tenant_normalized_registration",
        ),
        Index("ix_vehicles_tenant_id", "tenant_id"),
        Index("ix_vehicles_fleet_id", "fleet_id"),
        Index("ix_vehicles_truck_model_id", "truck_model_id"),
        Index("ix_vehicles_vehicle_status", "vehicle_status"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    tenant_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("tenants.id", ondelete="RESTRICT"),
        nullable=False,
    )
    fleet_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("fleets.id", ondelete="RESTRICT"),
        nullable=False,
    )
    truck_model_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("truck_models.id", ondelete="RESTRICT"),
        nullable=True,
    )
    registration_number: Mapped[str | None] = mapped_column(String(32), nullable=True)
    normalized_registration_number: Mapped[str | None] = mapped_column(String(32), nullable=True)
    registration_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    manufacturing_month_year: Mapped[date | None] = mapped_column(Date, nullable=True)
    gvw_kg: Mapped[int | None] = mapped_column(Integer, nullable=True)
    unladen_weight_kg: Mapped[int | None] = mapped_column(Integer, nullable=True)
    engine_cc: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cylinder_count: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    fuel_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    body_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    vehicle_status: Mapped[VehicleStatus] = mapped_column(
        Enum(VehicleStatus, name="vehicle_status", native_enum=False, length=32),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    tenant: Mapped[TenantModel] = relationship(back_populates="vehicles")
    fleet: Mapped[FleetModel] = relationship(back_populates="vehicles")
    truck_model: Mapped[TruckModelRecord | None] = relationship(back_populates="vehicles")
    attribute_provenance: Mapped[list[VehicleAttributeProvenanceModel]] = relationship(
        back_populates="vehicle"
    )


class RuleMasterModel(Base):
    __tablename__ = "rule_master"
    __table_args__ = (
        UniqueConstraint("rule_id", "version", name="uq_rule_master_rule_id_version"),
        Index("ix_rule_master_rule_type", "rule_type"),
        Index("ix_rule_master_active_priority", "active", "priority"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    rule_id: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    version: Mapped[str] = mapped_column(String(32), nullable=False)
    rule_type: Mapped[str] = mapped_column(String(64), nullable=False)
    expression: Mapped[dict] = mapped_column(JSONB, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    effective_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    author: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class VehicleAttributeProvenanceModel(Base):
    __tablename__ = "vehicle_attribute_provenance"
    __table_args__ = (
        Index("ix_vehicle_attribute_provenance_vehicle_id", "vehicle_id"),
        Index("ix_vehicle_attribute_provenance_tenant_id", "tenant_id"),
        Index(
            "ix_vehicle_attribute_provenance_vehicle_attribute",
            "vehicle_id",
            "attribute",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    tenant_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("tenants.id", ondelete="RESTRICT"),
        nullable=False,
    )
    vehicle_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("vehicles.id", ondelete="RESTRICT"),
        nullable=False,
    )
    attribute: Mapped[str] = mapped_column(String(64), nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(String(32), nullable=False)
    source_system: Mapped[str] = mapped_column(String(64), nullable=False)
    source_field: Mapped[str | None] = mapped_column(String(128), nullable=True)
    source_record_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    transformation_type: Mapped[str] = mapped_column(String(64), nullable=False)
    rule_id: Mapped[str] = mapped_column(String(64), nullable=False)
    rule_version: Mapped[str] = mapped_column(String(32), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    vehicle: Mapped[VehicleModel] = relationship(back_populates="attribute_provenance")
