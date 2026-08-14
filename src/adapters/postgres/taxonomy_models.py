from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, Integer, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from adapters.postgres.base import Base


class TaxonomyTermMixin:
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class RegulatoryCategoryModel(TaxonomyTermMixin, Base):
    __tablename__ = "regulatory_categories"
    __table_args__ = (UniqueConstraint("code", name="uq_regulatory_categories_code"),)


class TruckSegmentModel(TaxonomyTermMixin, Base):
    __tablename__ = "truck_segments"
    __table_args__ = (UniqueConstraint("code", name="uq_truck_segments_code"),)


class TruckConfigurationModel(TaxonomyTermMixin, Base):
    __tablename__ = "truck_configurations"
    __table_args__ = (UniqueConstraint("code", name="uq_truck_configurations_code"),)


class BodyTypeModel(TaxonomyTermMixin, Base):
    __tablename__ = "body_types"
    __table_args__ = (UniqueConstraint("code", name="uq_body_types_code"),)


class AxleConfigurationModel(TaxonomyTermMixin, Base):
    __tablename__ = "axle_configurations"
    __table_args__ = (UniqueConstraint("code", name="uq_axle_configurations_code"),)


class PowertrainModel(TaxonomyTermMixin, Base):
    __tablename__ = "powertrains"
    __table_args__ = (UniqueConstraint("code", name="uq_powertrains_code"),)


class TruckApplicationModel(TaxonomyTermMixin, Base):
    __tablename__ = "truck_applications"
    __table_args__ = (UniqueConstraint("code", name="uq_truck_applications_code"),)


TAXONOMY_MODELS = {
    "regulatory_categories": RegulatoryCategoryModel,
    "truck_segments": TruckSegmentModel,
    "truck_configurations": TruckConfigurationModel,
    "body_types": BodyTypeModel,
    "axle_configurations": AxleConfigurationModel,
    "powertrains": PowertrainModel,
    "truck_applications": TruckApplicationModel,
}
