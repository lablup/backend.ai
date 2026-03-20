"""convert global-scoped permissions to domain-scoped

Revision ID: 5a4e677aea42
Revises: ffcf0ed13a26
Create Date: 2026-03-20 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "5a4e677aea42"
down_revision = "ffcf0ed13a26"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    # (a) Query all active domain names
    domain_rows = conn.execute(sa.text("SELECT name FROM domains ORDER BY name")).fetchall()
    domain_names = [row[0] for row in domain_rows]

    if not domain_names:
        # No domains exist; just delete global rows since there's nowhere to convert them
        conn.execute(sa.text("DELETE FROM permissions WHERE scope_type = 'global'"))
        return

    # (b) Query all permission rows where scope_type='global'
    global_perms = conn.execute(
        sa.text(
            "SELECT id, role_id, entity_type, operation"
            " FROM permissions"
            " WHERE scope_type = 'global'"
        )
    ).fetchall()

    if not global_perms:
        return

    # (c) For each global permission × each domain, insert a domain-scoped row
    # ON CONFLICT DO NOTHING handles the unique constraint
    # (role_id, scope_type, scope_id, entity_type, operation)
    insert_stmt = sa.text(
        "INSERT INTO permissions (id, role_id, scope_type, scope_id, entity_type, operation)"
        " VALUES (uuid_generate_v4(), :role_id, 'domain', :scope_id, :entity_type, :operation)"
        " ON CONFLICT ON CONSTRAINT uq_permissions_role_scope_entity_op DO NOTHING"
    )

    for perm in global_perms:
        for domain_name in domain_names:
            conn.execute(
                insert_stmt,
                {
                    "role_id": str(perm[1]),
                    "scope_id": domain_name,
                    "entity_type": perm[2],
                    "operation": perm[3],
                },
            )

    # (d) Delete all global-scoped permission rows
    conn.execute(sa.text("DELETE FROM permissions WHERE scope_type = 'global'"))


def downgrade() -> None:
    # Global scope is deprecated and has no corresponding RBACElementType.
    # The conversion to domain-scoped permissions is not reversible because
    # we cannot determine which domain-scoped rows were originally global.
    pass
