"""reconcile index drift across install paths

A fresh install builds tables from the model metadata (`mgr schema oneshot`) and
stamps head without running a migration; an existing install replays the
migration files. Three indexes were created by migrations but never declared on
the models, so they existed only on migrated databases. This migration makes
every database agree with the models, in whichever direction each index earns.

Created here, because each backs a foreign key whose parent-side delete has to
find the referencing rows -- the index costs a write and saves a scan:
  - ix_role_invitations_invitee_user_id (users delete cascades)
  - ix_prometheus_query_presets_category_id (category delete sets null)

Dropped here, because nothing reads it: vfolders.creator_id carries no foreign
key and is never filtered, joined, or ordered by -- it is only written and
selected. Its creation has been removed from b4e7f1a2c3d5, so this drop is what
clears it from databases that already ran that revision.

The existence checks keep every statement a no-op where the database already
agrees.

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
    op.execute("DROP INDEX IF EXISTS ix_vfolders_creator_id")


def downgrade() -> None:
    # Intentionally a no-op. This migration exists to make the two install paths
    # agree with the models; undoing it would only put the drift back.
    pass
