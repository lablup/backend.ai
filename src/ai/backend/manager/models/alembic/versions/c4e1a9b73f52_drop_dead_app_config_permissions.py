"""drop_dead_app_config_permissions

Delete the ``APP_CONFIG`` permission rows left behind by the legacy AppConfig removal.

``app_config`` was granted as an RBAC resource type back when an ``app_configs`` table
existed. ``84d5c6daf8cc`` dropped that table (BA-5822, preparation for BEP-1052) along with
the model and the service, but left the entity type in ``_resource_types()`` and in the
role fixture, so the grants outlived the entity they guarded. Nothing resolves them: there
is no table, no model, no service, and no action declaring ``EntityType.APP_CONFIG``.

The BEP-1052 replacement does not revive it. The new AppConfig service owns no tables and
is not an RBAC target — it merges the allow-list entries visible to a user/domain, with no
RBAC validation. RBAC guards fragment writes (``app_config_fragment``) only.

Revision ID: c4e1a9b73f52
Revises: aa27f1d5cd35
Create Date: 2026-07-14 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.rbac_models.migration.enums import EntityType

# revision identifiers, used by Alembic.
revision = "c4e1a9b73f52"
down_revision = "aa27f1d5cd35"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None


def upgrade() -> None:
    db_conn = op.get_bind()
    db_conn.execute(
        sa.text("DELETE FROM permissions WHERE entity_type = :entity_type"),
        {"entity_type": EntityType.APP_CONFIG.value},
    )


def downgrade() -> None:
    # Not restored. The rows were written by a5e87ed3b6d4 through the `permission_groups`
    # schema, which f41bbe0c0f12 has since removed, so the original grants cannot be
    # reproduced. Re-inserting them would in any case grant nothing: no table, model,
    # service, or permission check resolves `app_config`.
    pass
