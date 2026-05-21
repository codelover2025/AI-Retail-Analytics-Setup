"""Initial Phase 1 schema (baseline — matches create_all models).

Revision ID: 001
Revises:
Create Date: 2026-05-21

Use for fresh Postgres deploys. Existing SQLite dev DBs may already have tables via init_db().
"""
from typing import Sequence, Union

from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Import metadata and create all tables (equivalent to init_db for migrations path)
    from shared.database.models import Base

    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    from shared.database.models import Base

    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
