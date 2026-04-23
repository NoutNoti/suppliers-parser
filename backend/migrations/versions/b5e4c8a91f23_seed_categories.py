"""seed categories

Revision ID: b5e4c8a91f23
Revises: a3f1d9e2c047
Create Date: 2026-04-23 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b5e4c8a91f23"
down_revision: Union[str, Sequence[str], None] = "a3f1d9e2c047"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
