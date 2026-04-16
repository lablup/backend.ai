"""fix email scope_ids to UUIDs in association_scopes_entities

For rows where scope_type='user' and scope_id contains an email address
instead of a UUID, resolve the email to the corresponding user UUID.

Revision ID: a1b2c3d4e5f6
Revises: 85743d601993
Create Date: 2026-04-16

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "a1b2c3d4e5f6"
down_revision = "85743d601993"
# Part of: 26.5.0
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text("""
        UPDATE association_scopes_entities AS ase
        SET scope_id = u.uuid::text
        FROM users u
        WHERE ase.scope_type = 'user'
          AND ase.scope_id = u.email
    """)
    )


def downgrade() -> None:
    # Cannot safely reverse: we don't know which rows had email values.
    pass
