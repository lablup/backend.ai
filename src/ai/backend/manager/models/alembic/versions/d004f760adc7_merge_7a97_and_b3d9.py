"""merge 7a97 and b3d9

Reconcile the two heads left on main by independent migrations
``7a9720934f55`` (usage-bucket resource group ids) and ``b3d9f7a2c184``
(APP_CONFIG_FRAGMENT RBAC permissions), which branched from a shared parent
without reconciling. Empty merge — no schema change.

Revision ID: d004f760adc7
Revises: 7a9720934f55, b3d9f7a2c184
Create Date: 2026-07-19

"""

# revision identifiers, used by Alembic.
revision = "d004f760adc7"
down_revision = ("7a9720934f55", "b3d9f7a2c184")
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
