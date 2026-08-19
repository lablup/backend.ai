"""backfill admin page read permission for runtime-created admin roles

The earlier backfill (3b6297b1bd75) matched admin roles only by the
data-migration naming scheme ``role_project_<id>_admin`` /
``role_domain_<name>_admin``. Admin roles created at runtime use a different
naming scheme (``project-<id8>-admin`` / ``domain-<name>-admin``) and were
therefore skipped, leaving them without the ``*_admin_page`` READ permission.

This migration backfills the missed READ permission for those runtime-named
admin roles. It is idempotent via ``ON CONFLICT DO NOTHING``.

Revision ID: f2b9a4c7e103
Revises: c7e1a9d4f6b2
Create Date: 2026-07-11 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "f2b9a4c7e103"
down_revision = "c7e1a9d4f6b2"
# Part of: 26.4.8 (backport), 26.8.0 (main)
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    # Insert READ permission for project_admin_page for every runtime-created
    # project admin role (named 'project-<id8>-admin'). Derive scope_type and
    # scope_id from existing permissions already held by each role.
    conn.execute(
        sa.text("""
        INSERT INTO permissions (role_id, scope_type, scope_id, entity_type, operation, permission)
        SELECT DISTINCT p.role_id, p.scope_type, p.scope_id, 'project_admin_page', 'read', 1
        FROM permissions p
        JOIN roles r ON r.id = p.role_id
        WHERE r.name LIKE 'project-%-admin'
          AND p.scope_type = 'project'
        ON CONFLICT DO NOTHING
    """)
    )

    # Insert READ permission for domain_admin_page for every runtime-created
    # domain admin role (named 'domain-<name>-admin').
    conn.execute(
        sa.text("""
        INSERT INTO permissions (role_id, scope_type, scope_id, entity_type, operation, permission)
        SELECT DISTINCT p.role_id, p.scope_type, p.scope_id, 'domain_admin_page', 'read', 1
        FROM permissions p
        JOIN roles r ON r.id = p.role_id
        WHERE r.name LIKE 'domain-%-admin'
          AND p.scope_type = 'domain'
        ON CONFLICT DO NOTHING
    """)
    )


def downgrade() -> None:
    # No-op: the admin-page READ permission is part of each admin role's intended
    # permission set (granted natively at role creation for roles created after the
    # fix). A pattern-based DELETE here cannot distinguish rows inserted by this
    # backfill from those granted at creation, so it would strip permissions the
    # roles legitimately hold. Leaving the backfilled rows in place is safe.
    pass
