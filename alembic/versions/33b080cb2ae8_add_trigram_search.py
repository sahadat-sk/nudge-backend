"""add trigram search

Revision ID: 33b080cb2ae8
Revises: d2e7ebefbca2
Create Date: 2026-06-29 10:08:33.826423

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '33b080cb2ae8'
down_revision: Union[str, Sequence[str], None] = 'd2e7ebefbca2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(
        "CREATE EXTENSION IF NOT EXISTS pg_trgm"
    )

    op.execute("""
        CREATE INDEX idx_contacts_name_trgm
        ON contacts
        USING gin (name gin_trgm_ops)
    """)


def downgrade() -> None:
    """Downgrade schema."""
    op.execute(
        "DROP INDEX IF EXISTS idx_contacts_name_trgm"
    )
