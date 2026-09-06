"""require a resolved recipient on an accepted share

An offer that reached an address names no scope until it is answered. Answering records
the scope that answered, so from that point an accepted row always names one and the
graph edge beside it has somewhere to hang.

Revision ID: e4c8b1d70a35
Revises: b6f2c1e94a30
Create Date: 2026-09-06 13:00:00

"""

# Part of: NEXT_RELEASE_VERSION

from typing import Final

from alembic import op

# revision identifiers, used by Alembic.
revision = "e4c8b1d70a35"
down_revision = "b6f2c1e94a30"
branch_labels = None
depends_on = None

_ACCEPTED_RESOLVED: Final = "accepted_resolved"


def upgrade() -> None:
    op.execute(
        "DELETE FROM entity_shares WHERE status = 'accepted' AND recipient_entity_type IS NULL"
    )
    op.create_check_constraint(
        _ACCEPTED_RESOLVED,
        "entity_shares",
        "status <> 'accepted' OR recipient_entity_type IS NOT NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        op.f(f"ck_entity_shares_{_ACCEPTED_RESOLVED}"), "entity_shares", type_="check"
    )
