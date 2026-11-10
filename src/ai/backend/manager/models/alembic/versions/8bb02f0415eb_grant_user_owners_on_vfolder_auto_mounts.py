"""Grant user owners every operation on vfolder auto-mounts

A user now sets auto-mounts on themself, so only the user owner may add, change or
remove them. Write the grants to the preset and to every role made from it.

Revision ID: 8bb02f0415eb
Revises: 91d276b3c15a
Create Date: 2026-10-27

"""

from __future__ import annotations

from typing import Final

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "8bb02f0415eb"  # Part of: NEXT_RELEASE_VERSION
down_revision = "91d276b3c15a"
branch_labels = None
depends_on = None


_PRESET_ID: Final[str] = "776c1366-dcf3-5abd-b8de-bc3ad3b759ad"
_ENTITY_TYPE: Final[str] = "vfolder_auto_mount"
_BITS: Final[tuple[int, ...]] = (1, 2, 4, 8, 16)


def grant(conn: sa.engine.Connection) -> None:
    params = [
        {"preset_id": _PRESET_ID, "entity_type": _ENTITY_TYPE, "permission": bit} for bit in _BITS
    ]
    conn.execute(
        sa.text("""
            INSERT INTO role_permission_presets (role_preset_id, entity_type, permission)
            SELECT p.id, :entity_type, :permission
            FROM role_presets p
            WHERE p.id = CAST(:preset_id AS uuid)
            ON CONFLICT DO NOTHING
        """),
        params,
    )
    conn.execute(
        sa.text("""
            INSERT INTO permissions (role_id, entity_type, permission)
            SELECT r.id, :entity_type, :permission
            FROM roles r
            WHERE r.role_preset_id = CAST(:preset_id AS uuid)
            ON CONFLICT (role_id, entity_type, permission) DO NOTHING
        """),
        params,
    )


def upgrade() -> None:
    grant(op.get_bind())


def downgrade() -> None:
    """The grants stay: taking them back takes away what users hold."""
