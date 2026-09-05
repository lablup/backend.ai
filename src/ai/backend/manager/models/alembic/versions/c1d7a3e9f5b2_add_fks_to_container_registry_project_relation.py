"""add foreign keys to the container registry project relation

Revision ID: c1d7a3e9f5b2
Revises: fa8236974782
Create Date: 2026-09-05 01:30:00.000000

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "c1d7a3e9f5b2"
down_revision = "fa8236974782"
branch_labels = None
depends_on = None

TABLE = "association_container_registries_groups"
# Shortened from the metadata naming convention, which would generate a 75-character
# name for the registry key — over PostgreSQL's 63-character limit. The Row declaration
# names both keys the same way.
FK_REGISTRY = f"fk_{TABLE}_registry_id"
FK_PROJECT = f"fk_{TABLE}_group_id"


def upgrade() -> None:
    op.execute(
        f"DELETE FROM {TABLE} a"
        " WHERE NOT EXISTS (SELECT 1 FROM container_registries r WHERE r.id = a.registry_id)"
        "    OR NOT EXISTS (SELECT 1 FROM groups g WHERE g.id = a.group_id)"
    )
    op.execute(f"ALTER TABLE {TABLE} DROP CONSTRAINT IF EXISTS {FK_REGISTRY}")
    op.execute(f"ALTER TABLE {TABLE} DROP CONSTRAINT IF EXISTS {FK_PROJECT}")
    op.create_foreign_key(
        FK_REGISTRY, TABLE, "container_registries", ["registry_id"], ["id"], ondelete="CASCADE"
    )
    op.create_foreign_key(FK_PROJECT, TABLE, "groups", ["group_id"], ["id"], ondelete="CASCADE")


def downgrade() -> None:
    op.execute(f"ALTER TABLE {TABLE} DROP CONSTRAINT IF EXISTS {FK_REGISTRY}")
    op.execute(f"ALTER TABLE {TABLE} DROP CONSTRAINT IF EXISTS {FK_PROJECT}")
