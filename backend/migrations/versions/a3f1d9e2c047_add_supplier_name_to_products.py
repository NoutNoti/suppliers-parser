"""add supplier_name to products

Revision ID: a3f1d9e2c047
Revises: 7128c6983ee1
Create Date: 2026-04-22 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a3f1d9e2c047"
down_revision: Union[str, Sequence[str], None] = "7128c6983ee1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "products",
        sa.Column("supplier_name", sa.String(length=255), nullable=True),
    )
    op.create_index(
        "ix_products_supplier_name", "products", ["supplier_name"], unique=False
    )
    # Унікальний індекс для ON CONFLICT DO UPDATE по (external_id, supplier_name).
    # NULL-значення не конфліктують між собою (поведінка PostgreSQL),
    # тому товари без external_id/supplier_name завжди вставляються як нові.
    op.create_index(
        "uix_products_external_id_supplier_name",
        "products",
        ["external_id", "supplier_name"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("uix_products_external_id_supplier_name", table_name="products")
    op.drop_index("ix_products_supplier_name", table_name="products")
    op.drop_column("products", "supplier_name")
