"""Assign every user the public_member role

Grant each existing user the role the public_member preset created in the public global
entity.

Revision ID: d6e2b7a4c913
Revises: c90c18a859a2
Create Date: 2026-09-18

"""

from __future__ import annotations

from typing import Final

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "d6e2b7a4c913"  # Part of: NEXT_RELEASE_VERSION
down_revision = "c90c18a859a2"
branch_labels = None
depends_on = None


_PRESET_ID: Final[str] = "01993d56-bb39-7d13-a84b-b6a84fc8b7fd"


def assign_roles(conn: sa.engine.Connection) -> None:
    """Give every user the roles the public_member preset instantiated, as creating a
    user does: an active role the scope assigns on its own."""
    conn.execute(
        sa.text("""
            INSERT INTO user_roles (user_id, role_id)
            SELECT u.uuid, r.id
            FROM roles r
            CROSS JOIN users u
            WHERE r.role_preset_id = CAST(:id AS uuid)
              AND r.auto_assign IS TRUE
              AND r.status = 'active'
            ON CONFLICT (user_id, role_id) DO NOTHING
        """).bindparams(id=_PRESET_ID)
    )


def upgrade() -> None:
    assign_roles(op.get_bind())


def downgrade() -> None:
    """The assignments stay: taking them back takes away what users hold."""
