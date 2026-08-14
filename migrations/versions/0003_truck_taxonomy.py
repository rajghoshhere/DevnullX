"""truck taxonomy reference tables and truck_model foreign keys

Revision ID: 0003_truck_taxonomy
Revises: 0002_core_domain_model
Create Date: 2026-08-14

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003_truck_taxonomy"
down_revision: Union[str, None] = "0002_core_domain_model"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLES = (
    "regulatory_categories",
    "truck_segments",
    "truck_configurations",
    "body_types",
    "axle_configurations",
    "powertrains",
    "truck_applications",
)

TRUCK_MODEL_FKS = (
    ("regulatory_category_id", "regulatory_categories"),
    ("truck_segment_id", "truck_segments"),
    ("truck_configuration_id", "truck_configurations"),
    ("body_type_id", "body_types"),
    ("axle_configuration_id", "axle_configurations"),
    ("powertrain_id", "powertrains"),
    ("truck_application_id", "truck_applications"),
)


def upgrade() -> None:
    for table_name in TABLES:
        op.create_table(
            table_name,
            sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
            sa.Column("code", sa.String(length=64), nullable=False),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("code", name=f"uq_{table_name}_code"),
        )

    for column_name, target_table in TRUCK_MODEL_FKS:
        op.add_column(
            "truck_models",
            sa.Column(column_name, sa.Uuid(as_uuid=True), nullable=True),
        )
        op.create_foreign_key(
            f"fk_truck_models_{column_name}",
            "truck_models",
            target_table,
            [column_name],
            ["id"],
            ondelete="RESTRICT",
        )
        op.create_index(f"ix_truck_models_{column_name}", "truck_models", [column_name])


def downgrade() -> None:
    for column_name, _target_table in reversed(TRUCK_MODEL_FKS):
        op.drop_index(f"ix_truck_models_{column_name}", table_name="truck_models")
        op.drop_constraint(f"fk_truck_models_{column_name}", "truck_models", type_="foreignkey")
        op.drop_column("truck_models", column_name)

    for table_name in reversed(TABLES):
        op.drop_table(table_name)
