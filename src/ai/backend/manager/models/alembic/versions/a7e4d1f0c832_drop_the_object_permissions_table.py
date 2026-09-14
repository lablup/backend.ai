"""Drop the object permissions table

``object_permissions`` has no reader left. Nothing writes it, no route reaches it,
and the role detail it was loaded into never carried it outside the manager. The
per-entity grants it once held are answered by the virtual entity graph.

The downgrade recreates the table empty.

Create Date: 2026-09-10

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID

# revision identifiers, used by Alembic.
revision = "a7e4d1f0c832"
down_revision = "b3c81f0a49d5"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_table("object_permissions")


def downgrade() -> None:
    op.create_table(
        "object_permissions",
        sa.Column("id", GUID(), server_default=sa.text("uuid_generate_v7()"), nullable=False),
        sa.Column("role_id", GUID(), nullable=False),
        sa.Column("entity_type", sa.String(length=32), nullable=False),
        sa.Column("entity_id", sa.String(length=64), nullable=False),
        sa.Column("operation", sa.String(length=32), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_object_permissions")),
        sa.UniqueConstraint(
            "role_id",
            "entity_type",
            "entity_id",
            "operation",
            name="uq_object_permissions_role_entity_op",
        ),
    )
    op.create_index(
        "ix_id_role_id_entity_id",
        "object_permissions",
        ["id", "role_id", "entity_id"],
    )
