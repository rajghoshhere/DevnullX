"""rule_master and vehicle_attribute_provenance

Revision ID: 0004_rule_engine
Revises: 0003_truck_taxonomy
Create Date: 2026-08-14

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004_rule_engine"
down_revision: Union[str, None] = "0003_truck_taxonomy"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "rule_master",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("rule_id", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("version", sa.String(length=32), nullable=False),
        sa.Column("rule_type", sa.String(length=64), nullable=False),
        sa.Column("expression", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=True),
        sa.Column("effective_to", sa.DateTime(timezone=True), nullable=True),
        sa.Column("author", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("rule_id", "version", name="uq_rule_master_rule_id_version"),
    )
    op.create_index("ix_rule_master_rule_type", "rule_master", ["rule_type"])
    op.create_index("ix_rule_master_active_priority", "rule_master", ["active", "priority"])

    op.create_table(
        "vehicle_attribute_provenance",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("tenant_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("vehicle_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("attribute", sa.String(length=64), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("source_system", sa.String(length=64), nullable=False),
        sa.Column("source_field", sa.String(length=128), nullable=True),
        sa.Column("source_record_id", sa.String(length=128), nullable=True),
        sa.Column("transformation_type", sa.String(length=64), nullable=False),
        sa.Column("rule_id", sa.String(length=64), nullable=False),
        sa.Column("rule_version", sa.String(length=32), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["vehicle_id"], ["vehicles.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_vehicle_attribute_provenance_vehicle_id",
        "vehicle_attribute_provenance",
        ["vehicle_id"],
    )
    op.create_index(
        "ix_vehicle_attribute_provenance_tenant_id",
        "vehicle_attribute_provenance",
        ["tenant_id"],
    )
    op.create_index(
        "ix_vehicle_attribute_provenance_vehicle_attribute",
        "vehicle_attribute_provenance",
        ["vehicle_id", "attribute"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_vehicle_attribute_provenance_vehicle_attribute",
        table_name="vehicle_attribute_provenance",
    )
    op.drop_index(
        "ix_vehicle_attribute_provenance_tenant_id",
        table_name="vehicle_attribute_provenance",
    )
    op.drop_index(
        "ix_vehicle_attribute_provenance_vehicle_id",
        table_name="vehicle_attribute_provenance",
    )
    op.drop_table("vehicle_attribute_provenance")
    op.drop_index("ix_rule_master_active_priority", table_name="rule_master")
    op.drop_index("ix_rule_master_rule_type", table_name="rule_master")
    op.drop_table("rule_master")
