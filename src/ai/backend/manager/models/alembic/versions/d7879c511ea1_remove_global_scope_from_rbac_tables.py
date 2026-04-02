"""remove global scope rows from RBAC tables

Revision ID: d7879c511ea1
Revises: 3727dd0927cf
Create Date: 2026-03-24 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "d7879c511ea1"
down_revision = "3727dd0927cf"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("DELETE FROM association_scopes_entities WHERE scope_type = 'global'"))


def downgrade() -> None:
    pass
