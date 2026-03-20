"""convert global-scoped permissions to domain-scoped

Revision ID: 5a4e677aea42
Revises: 0e0723286a7a
Create Date: 2026-03-20 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "5a4e677aea42"
down_revision = "0e0723286a7a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    # Convert global-scoped permissions to domain-scoped by creating one row
    # per active domain for each global permission row.
    # ON CONFLICT DO NOTHING handles the unique constraint
    # (role_id, scope_type, scope_id, entity_type, operation).
    conn.execute(
        sa.text(
            "INSERT INTO permissions (id, role_id, scope_type, scope_id, entity_type, operation)"
            " SELECT uuid_generate_v4(), p.role_id, 'domain', d.name, p.entity_type, p.operation"
            " FROM permissions AS p"
            " CROSS JOIN domains AS d"
            " WHERE p.scope_type = 'global' AND d.is_active IS TRUE"
            " ON CONFLICT ON CONSTRAINT uq_permissions_role_scope_entity_op DO NOTHING"
        )
    )

    # Delete all global-scoped permission rows now that they are converted
    conn.execute(sa.text("DELETE FROM permissions WHERE scope_type = 'global'"))


def downgrade() -> None:
    # Global scope is deprecated and has no corresponding RBACElementType.
    # The conversion to domain-scoped permissions is not reversible because
    # we cannot determine which domain-scoped rows were originally global.
    pass
