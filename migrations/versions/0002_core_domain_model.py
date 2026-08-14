"""core domain tables: fleet owners, fleets, manufacturers, truck models, vehicles

Revision ID: 0002_core_domain_model
Revises: 0001_create_tenants
Create Date: 2026-08-14

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002_core_domain_model"
down_revision: Union[str, None] = "0001_create_tenants"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "tenants",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.alter_column("tenants", "updated_at", server_default=None)

    op.create_table(
        "fleet_owners",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("tenant_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_fleet_owners_tenant_id", "fleet_owners", ["tenant_id"])

    op.create_table(
        "fleets",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("tenant_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_fleets_tenant_id", "fleets", ["tenant_id"])

    op.create_table(
        "manufacturers",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "truck_models",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("manufacturer_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["manufacturer_id"], ["manufacturers.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_truck_models_manufacturer_id", "truck_models", ["manufacturer_id"])

    op.create_table(
        "vehicles",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("tenant_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("fleet_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("truck_model_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("registration_number", sa.String(length=32), nullable=True),
        sa.Column("normalized_registration_number", sa.String(length=32), nullable=True),
        sa.Column("registration_date", sa.Date(), nullable=True),
        sa.Column("manufacturing_month_year", sa.Date(), nullable=True),
        sa.Column("gvw_kg", sa.Integer(), nullable=True),
        sa.Column("unladen_weight_kg", sa.Integer(), nullable=True),
        sa.Column("engine_cc", sa.Integer(), nullable=True),
        sa.Column("cylinder_count", sa.SmallInteger(), nullable=True),
        sa.Column("fuel_type", sa.String(length=32), nullable=True),
        sa.Column("body_type", sa.String(length=32), nullable=True),
        sa.Column("vehicle_status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["fleet_id"], ["fleets.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["truck_model_id"], ["truck_models.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id",
            "normalized_registration_number",
            name="uq_vehicles_tenant_normalized_registration",
        ),
    )
    op.create_index("ix_vehicles_tenant_id", "vehicles", ["tenant_id"])
    op.create_index("ix_vehicles_fleet_id", "vehicles", ["fleet_id"])
    op.create_index("ix_vehicles_truck_model_id", "vehicles", ["truck_model_id"])
    op.create_index("ix_vehicles_vehicle_status", "vehicles", ["vehicle_status"])


def downgrade() -> None:
    op.drop_index("ix_vehicles_vehicle_status", table_name="vehicles")
    op.drop_index("ix_vehicles_truck_model_id", table_name="vehicles")
    op.drop_index("ix_vehicles_fleet_id", table_name="vehicles")
    op.drop_index("ix_vehicles_tenant_id", table_name="vehicles")
    op.drop_table("vehicles")
    op.drop_index("ix_truck_models_manufacturer_id", table_name="truck_models")
    op.drop_table("truck_models")
    op.drop_table("manufacturers")
    op.drop_index("ix_fleets_tenant_id", table_name="fleets")
    op.drop_table("fleets")
    op.drop_index("ix_fleet_owners_tenant_id", table_name="fleet_owners")
    op.drop_table("fleet_owners")
    op.drop_column("tenants", "updated_at")
