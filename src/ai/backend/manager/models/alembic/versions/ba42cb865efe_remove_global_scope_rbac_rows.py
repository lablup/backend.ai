"""remove global-scoped RBAC rows from permissions and association_scopes_entities

The ``global`` scope_type is deprecated and has no corresponding
``RBACElementType``. Existing rows leak through the GQL ``adminPermissions``
adapter and raise ``RBACTypeConversionError`` (see BA-6059).

A previous migration (``5a4e677aea42``) cleaned ``permissions`` once but rows
re-appeared via fixture loads. ``d7879c511ea1`` only partially cleaned
``association_scopes_entities``. This migration removes any remaining
``scope_type = 'global'`` rows from both tables and is safe to re-apply.

Revision ID: ba42cb865efe
Revises: b2d4f6e8c1a3
Create Date: 2026-05-15

"""

# Part of: 26.5.0

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "ba42cb865efe"
down_revision = "b2d4f6e8c1a3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("DELETE FROM permissions WHERE scope_type = 'global'"))
    conn.execute(sa.text("DELETE FROM association_scopes_entities WHERE scope_type = 'global'"))


def downgrade() -> None:
    # Global scope is deprecated and has no corresponding RBACElementType.
    # The deletion is not reversible because the original scope_id and entity
    # mappings are not preserved.
    pass
