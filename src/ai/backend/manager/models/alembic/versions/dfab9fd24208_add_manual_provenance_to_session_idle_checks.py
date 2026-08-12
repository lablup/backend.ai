"""add manual provenance to session_idle_checks

Mark rows written by the exclusion/inclusion user APIs (is_manual, plus
who triggered them) so assignment sync only deletes its own rows
(BA-7339).

Revision ID: dfab9fd24208
Revises: c8d51e7a3b62
Create Date: 2026-08-12 14:42:45.963593

"""

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID

# revision identifiers, used by Alembic.
revision = "dfab9fd24208"
down_revision = "c8d51e7a3b62"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "session_idle_checks",
        sa.Column(
            "is_manual",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column(
        "session_idle_checks",
        sa.Column("manually_triggered_by", GUID, nullable=True),
    )
    op.create_foreign_key(
        "fk_session_idle_checks_manually_triggered_by",
        "session_idle_checks",
        "users",
        ["manually_triggered_by"],
        ["uuid"],
        ondelete="SET NULL",
    )
    op.create_check_constraint(
        "manual_trigger",
        "session_idle_checks",
        "manually_triggered_by IS NULL OR is_manual",
    )


def downgrade() -> None:
    # The ck naming convention templates explicit names, so pass the short name.
    op.drop_constraint(
        "manual_trigger",
        "session_idle_checks",
        type_="check",
    )
    op.drop_constraint(
        "fk_session_idle_checks_manually_triggered_by",
        "session_idle_checks",
        type_="foreignkey",
    )
    op.drop_column("session_idle_checks", "manually_triggered_by")
    op.drop_column("session_idle_checks", "is_manual")
