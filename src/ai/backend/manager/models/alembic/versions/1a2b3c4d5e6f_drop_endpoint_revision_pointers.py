"""drop current_revision / deploying_revision from endpoints

The revision pointers now live on the replica groups:

- current revision  = primary group's ``current_revision_id``
- deploying revision = target group's ``target_revision_id``

The ``endpoints.current_revision`` / ``deploying_revision`` columns are no
longer read or written, so drop them. ``downgrade`` re-adds the columns and
back-fills them from the replica groups.

Create Date: 2026-05-30
"""

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID

revision = "1a2b3c4d5e6f"
down_revision = "c0ffee5a91d3"
# Part of: 26.6.0
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column("endpoints", "current_revision")
    op.drop_column("endpoints", "deploying_revision")


def downgrade() -> None:
    op.add_column("endpoints", sa.Column("current_revision", GUID(), nullable=True))
    op.add_column("endpoints", sa.Column("deploying_revision", GUID(), nullable=True))
    # Back-fill from the replica groups.
    op.execute("""
        UPDATE endpoints e
        SET current_revision = rg.current_revision_id
        FROM replica_groups rg
        WHERE e.primary_replica_group_id = rg.id
    """)
    op.execute("""
        UPDATE endpoints e
        SET deploying_revision = rg.target_revision_id
        FROM replica_groups rg
        WHERE e.target_replica_group_id = rg.id
    """)
