"""add admin page read permissions to existing admin roles

Revision ID: 3b6297b1bd75
Revises: cf3290640ea8
Create Date: 2026-03-24 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "3b6297b1bd75"
down_revision = "cf3290640ea8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    # Insert READ permission for project_admin_page for every project admin role.
    # Derive scope_type and scope_id from existing permissions already held by each role.
    conn.execute(
        sa.text("""
        INSERT INTO permissions (role_id, scope_type, scope_id, entity_type, operation)
        SELECT DISTINCT p.role_id, p.scope_type, p.scope_id, 'project_admin_page', 'read'
        FROM permissions p
        JOIN roles r ON r.id = p.role_id
        WHERE r.name LIKE 'role\\_project\\_%\\_admin'
          AND p.scope_type = 'project'
        ON CONFLICT DO NOTHING
    """)
    )

    # Insert READ permission for domain_admin_page for every domain admin role.
    conn.execute(
        sa.text("""
        INSERT INTO permissions (role_id, scope_type, scope_id, entity_type, operation)
        SELECT DISTINCT p.role_id, p.scope_type, p.scope_id, 'domain_admin_page', 'read'
        FROM permissions p
        JOIN roles r ON r.id = p.role_id
        WHERE r.name LIKE 'role\\_domain\\_%\\_admin'
          AND p.scope_type = 'domain'
        ON CONFLICT DO NOTHING
    """)
    )


def downgrade() -> None:
    # Forward-only: the seeded rows are indistinguishable from ones granted
    # afterwards, so deleting by entity_type would erase operator-managed grants.
    pass
