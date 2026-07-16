"""backfill indexes missing on fresh installs

Two migrations create an index that the matching model never declared, so the
index only ever existed on databases built by replaying migrations. Databases
built by `mgr schema oneshot` -- which creates tables from the model metadata and
stamps head -- never got them. The models now declare both, which covers new
installs; this migration heals the ones already out there.

Both cover a foreign key column whose parent-side delete has to find the
referencing rows, so the index earns its write cost.

IF NOT EXISTS keeps it a no-op on migrated databases, which already have them.

Revision ID: b2f7c1a94e30
Revises: aa27f1d5cd35
Create Date: 2026-07-16

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "b2f7c1a94e30"
down_revision = "aa27f1d5cd35"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_role_invitations_invitee_user_id"
        " ON role_invitations (invitee_user_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_prometheus_query_presets_category_id"
        " ON prometheus_query_presets (category_id)"
    )


def downgrade() -> None:
    # Intentionally a no-op. These indexes are part of the schema the models
    # declare, so dropping them here would recreate the very drift this
    # migration exists to remove -- and would strand the revisions that create
    # them, whose downgrades expect them to be present.
    pass
