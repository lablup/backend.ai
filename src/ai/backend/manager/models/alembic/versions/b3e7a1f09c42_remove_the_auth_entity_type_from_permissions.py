"""Remove the auth entity type from the permissions

`auth` is no longer an entity type: the operations it named are wired under `global` or
`user`. Drop the permission rows and the preset permission rows that still name it.

Revision ID: b3e7a1f09c42
Revises: dc61fa027fc1
Create Date: 2026-09-15

"""

from __future__ import annotations

from typing import Final

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "b3e7a1f09c42"
down_revision = "dc61fa027fc1"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None


_RETIRED_ENTITY_TYPE: Final[str] = "auth"


def remove_retired_permissions(conn: sa.engine.Connection) -> None:
    conn.execute(
        sa.text("DELETE FROM permissions WHERE entity_type = :name").bindparams(
            name=_RETIRED_ENTITY_TYPE
        )
    )
    conn.execute(
        sa.text("DELETE FROM role_permission_presets WHERE entity_type = :name").bindparams(
            name=_RETIRED_ENTITY_TYPE
        )
    )


def upgrade() -> None:
    remove_retired_permissions(op.get_bind())


def downgrade() -> None:
    # The removed rows named no entity type this build loads, so none is restored.
    pass
