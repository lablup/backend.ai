"""remove deprecated RBAC permission rows (global scope, session:app entity)

Two classes of deprecated values leak through the GQL ``adminPermissions``
adapter and break the query (see BA-6059):

- ``scope_type = 'global'`` -- has no corresponding ``RBACElementType``,
  raising ``RBACTypeConversionError`` in the adapter.
- ``entity_type = 'session:app'`` -- renamed to ``session:app_service`` in
  the ``EntityType`` enum; existing rows fail StrEnum hydration at the ORM
  layer with ``ValueError: 'session:app' is not a valid EntityType``.

Earlier migrations (``5a4e677aea42``, ``d7879c511ea1``) only partially
addressed the global-scope leftovers. This migration removes any remaining
rows for both deprecated values and is safe to re-apply.

Revision ID: ba42cb865efe
Revises: c3d4e5f6a7b8
Create Date: 2026-05-15

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "ba42cb865efe"
down_revision = "c3d4e5f6a7b8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("DELETE FROM permissions WHERE scope_type = 'global'"))
    conn.execute(sa.text("DELETE FROM association_scopes_entities WHERE scope_type = 'global'"))
    conn.execute(sa.text("DELETE FROM permissions WHERE entity_type = 'session:app'"))


def downgrade() -> None:
    # Deprecated values have no corresponding RBAC element type and the
    # deletions are not reversible because original scope_id / entity_id
    # mappings are not preserved.
    pass
