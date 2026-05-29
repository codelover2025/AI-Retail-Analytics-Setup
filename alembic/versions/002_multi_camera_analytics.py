"""Multi-camera analytics tables.

Revision ID: 002
Revises: 001
Create Date: 2026-05-29
"""
from typing import Sequence, Union

from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    from shared.database.analytics_models import Base

    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    from shared.database.analytics_models import (
        AnalyticsSession,
        FootfallDailyCamera,
        Interaction,
        ZoneLog,
    )

    for table in (
        FootfallDailyCamera.__table__,
        Interaction.__table__,
        ZoneLog.__table__,
        AnalyticsSession.__table__,
    ):
        table.drop(bind=op.get_bind(), checkfirst=True)
