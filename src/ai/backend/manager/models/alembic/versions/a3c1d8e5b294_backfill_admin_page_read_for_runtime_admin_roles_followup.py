"""backfill admin page read permission for runtime-created admin roles (followup)

Idempotent duplicate of f2b9a4c7e103 appended on top of the main head so that
databases already at the main head — which never applied f2b9a4c7e103 (it was
spliced in earlier on the chain) — still receive the backfill. It is a no-op on
databases that already applied f2b9a4c7e103, via ``ON CONFLICT DO NOTHING``.

Revision ID: a3c1d8e5b294
Revises: c05f9465a9cd
Create Date: 2026-07-11 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "a3c1d8e5b294"
down_revision = "c05f9465a9cd"
# Part of: 26.4.8 (backport), 26.8.0 (main)
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    # Same backfill as f2b9a4c7e103, written idempotently.
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
    # The corresponding downgrade is handled by f2b9a4c7e103.
    pass
