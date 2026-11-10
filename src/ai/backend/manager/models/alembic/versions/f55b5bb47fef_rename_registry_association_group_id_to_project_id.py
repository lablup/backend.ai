"""Rename the registry association's group_id column to project_id."""

from alembic import op

revision = "f55b5bb47fef"
down_revision = "e8b41c6d2f73"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "association_container_registries_groups", "group_id", new_column_name="project_id"
    )
    op.execute(
        "ALTER TABLE association_container_registries_groups "
        "RENAME CONSTRAINT fk_association_container_registries_groups_group_id "
        "TO fk_association_container_registries_groups_project_id"
    )
    op.execute(
        "ALTER TABLE association_container_registries_groups "
        "RENAME CONSTRAINT uq_registry_id_group_id TO uq_registry_id_project_id"
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE association_container_registries_groups "
        "RENAME CONSTRAINT uq_registry_id_project_id TO uq_registry_id_group_id"
    )
    op.execute(
        "ALTER TABLE association_container_registries_groups "
        "RENAME CONSTRAINT fk_association_container_registries_groups_project_id "
        "TO fk_association_container_registries_groups_group_id"
    )
    op.alter_column(
        "association_container_registries_groups", "project_id", new_column_name="group_id"
    )
