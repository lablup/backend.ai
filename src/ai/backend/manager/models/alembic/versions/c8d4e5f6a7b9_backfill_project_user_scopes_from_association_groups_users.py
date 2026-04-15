"""backfill project-user scopes from association_groups_users

Copies every (user_id, group_id) row in ``association_groups_users`` into
``association_scopes_entities`` as a project-scope user membership with
``relation_type='ref'`` (per BEP-1048: Project ─ref─► User).

The statement is a single ``INSERT ... SELECT ... ON CONFLICT DO NOTHING``
keyed on the ``uq_scope_id_entity_id`` unique constraint, so it is
idempotent and naturally deduplicates the source rows. Inactive users or
groups are migrated as-is: the legacy table never filtered on ``is_active``,
and RBAC lookups against the new table must return the same membership set
that the legacy table does.

Revision ID: c8d4e5f6a7b9
Revises: a3b4c5d6e7f8
Create Date: 2026-04-14

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "c8d4e5f6a7b9"
down_revision = "a3b4c5d6e7f8"
# Part of: 26.3.0
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        INSERT INTO association_scopes_entities
            (scope_type, scope_id, entity_type, entity_id, relation_type)
        SELECT
            'project',
            group_id::text,
            'user',
            user_id::text,
            'ref'
        FROM association_groups_users
        ON CONFLICT ON CONSTRAINT uq_scope_id_entity_id DO NOTHING
    """)


def downgrade() -> None:
    # No-op: association_scopes_entities rows may also be produced by the
    # auto-sync path once it lands, so we cannot distinguish backfilled rows
    # from live ones at downgrade time. Dropping the table column or the
    # entire feature is handled by its own schema migration.
    pass
