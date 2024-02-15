"""rename_group_to_project

Revision ID: 5a2cd9a49a30
Revises: a5319bfc7d7c
Create Date: 2023-10-06 13:58:25.940687

"""

import enum
import textwrap

import sqlalchemy as sa
from alembic import op
from sqlalchemy.sql import text

from ai.backend.manager.models.base import convention
from ai.backend.manager.models.vfolder import VFolderOwnershipType, vfolders

# revision identifiers, used by Alembic.
revision = "5a2cd9a49a30"
down_revision = "a5319bfc7d7c"
branch_labels = None
depends_on = None


metadata = sa.MetaData(naming_convention=convention)
enum_name = VFolderOwnershipType.__name__.lower()

PAGE_SIZE = 100


class LegacyVFolderOwnershipType(str, enum.Enum):
    USER = "user"
    GROUP = "group"


new_values = set([role.value for role in VFolderOwnershipType])
legacy_values = set([role.value for role in LegacyVFolderOwnershipType])

new_names = new_values - legacy_values
legacy_names = legacy_values - new_values


def _delete_enum_value(connection, enum_name, val):
    connection.execute(
        text(
            textwrap.dedent(
                f"""DELETE FROM pg_enum
                    WHERE enumlabel = '{val}'
                    AND enumtypid = (
                    SELECT oid FROM pg_type WHERE typname = '{enum_name}'
                );"""
            )
        )
    )


def upgrade():
    conn = op.get_bind()

    # Drop indexes and constraints
    # sgroups_for_group
    op.drop_index("ix_sgroups_for_groups_group", table_name="sgroups_for_groups")
    op.drop_index("ix_sgroups_for_groups_scaling_group", table_name="sgroups_for_groups")
    op.drop_constraint(
        "fk_sgroups_for_groups_group_groups", "sgroups_for_groups", type_="foreignkey"
    )
    op.drop_constraint(
        "fk_sgroups_for_groups_scaling_group_scaling_groups",
        "sgroups_for_groups",
        type_="foreignkey",
    )
    # groups
    op.drop_constraint("uq_groups_name_domain_name", "groups", type_="unique")
    op.drop_index("ix_groups_domain_name", table_name="groups")
    # vfolders
    op.drop_constraint("fk_vfolders_group_groups", "vfolders", type_="foreignkey")
    # kernels
    op.drop_constraint("fk_kernels_group_id_groups", "kernels", type_="foreignkey")
    # sessions
    op.drop_constraint("fk_sessions_group_id_groups", "sessions", type_="foreignkey")
    # session_templates
    op.drop_constraint(
        "fk_session_templates_group_id_groups", "session_templates", type_="foreignkey"
    )
    # endpoints
    op.drop_constraint("fk_endpoints_project_groups", "endpoints", type_="foreignkey")
    # association_*_users
    op.drop_constraint(
        "uq_association_user_id_group_id",
        "association_groups_users",
        type_="unique",
    )
    op.drop_constraint(
        "fk_association_groups_users_group_id_groups",
        "association_groups_users",
        type_="foreignkey",
    )

    # Rename tables
    op.rename_table("groups", "projects")
    op.rename_table("association_groups_users", "association_projects_users")
    op.rename_table("sgroups_for_groups", "sgroups_for_projects")

    # Alter columns
    op.alter_column("kernels", column_name="group_id", new_column_name="project_id")
    op.alter_column("sessions", column_name="group_id", new_column_name="project_id")
    op.alter_column("session_templates", column_name="group_id", new_column_name="project_id")
    op.alter_column("vfolders", column_name="group", new_column_name="project_id")
    op.alter_column("endpoints", column_name="project", new_column_name="project_id")
    op.alter_column("sgroups_for_projects", column_name="group", new_column_name="project")
    op.alter_column(
        "association_projects_users", column_name="group_id", new_column_name="project_id"
    )

    # Create indexes and constraints
    # sgroups_for_group
    op.create_index(
        "ix_sgroups_for_projects_scaling_group",
        "sgroups_for_projects",
        ["scaling_group"],
        unique=False,
    )
    op.create_index(
        "ix_sgroups_for_projects_project", "sgroups_for_projects", ["project"], unique=False
    )
    op.create_foreign_key(
        op.f("fk_sgroups_for_projects_project_projects"),
        "sgroups_for_projects",
        "projects",
        ["project"],
        ["id"],
        onupdate="CASCADE",
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        op.f("fk_sgroups_for_projects_scaling_group_scaling_groups"),
        "sgroups_for_projects",
        "scaling_groups",
        ["scaling_group"],
        ["name"],
        onupdate="CASCADE",
        ondelete="CASCADE",
    )
    # projects
    op.create_unique_constraint("uq_projects_name_domain_name", "projects", ["name", "domain_name"])
    op.create_index("ix_projects_domain_name", "projects", ["domain_name"], unique=False)
    # vfolders
    op.create_foreign_key(
        op.f("fk_vfolders_project_id_projects"), "vfolders", "projects", ["project_id"], ["id"]
    )
    # kernels
    op.create_foreign_key(
        op.f("fk_kernels_project_id_projects"), "kernels", "projects", ["project_id"], ["id"]
    )
    # sessions
    op.create_foreign_key(
        op.f("fk_sessions_project_id_projects"), "sessions", "projects", ["project_id"], ["id"]
    )
    # session_templates
    op.create_foreign_key(
        op.f("fk_session_templates_project_id_projects"),
        "session_templates",
        "projects",
        ["project_id"],
        ["id"],
    )
    # endpoints
    op.create_foreign_key(
        op.f("fk_endpoints_project_id_projects"),
        "endpoints",
        "projects",
        ["project_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    # association_*_users
    op.create_foreign_key(
        op.f("fk_association_projects_users_project_id_projects"),
        "association_projects_users",
        "projects",
        ["project_id"],
        ["id"],
        onupdate="CASCADE",
        ondelete="CASCADE",
    )
    op.create_unique_constraint(
        "uq_association_user_id_project_id", "association_projects_users", ["user_id", "project_id"]
    )

    for n in new_names:
        conn.execute(text(f"ALTER TYPE {enum_name} ADD VALUE '{n}';"))
    conn.commit()

    while True:
        vfolder_query = (
            sa.select([vfolders.c.id])
            .select_from(vfolders)
            .where(vfolders.c.ownership_type == LegacyVFolderOwnershipType.GROUP)
            .limit(PAGE_SIZE)
        )

        update_query = (
            sa.update(vfolders)
            .values(ownership_type=VFolderOwnershipType.PROJECT)
            .where(vfolders.c.id.in_(vfolder_query))
        )
        result = conn.execute(update_query)
        if result.rowcount < PAGE_SIZE:
            break

    for n in legacy_names:
        _delete_enum_value(conn, enum_name, n)
    conn.commit()
    # ### end Alembic commands ###


def downgrade():
    conn = op.get_bind()

    # Drop indexes and constraints
    # sgroups_for_group
    op.drop_index("ix_sgroups_for_projects_scaling_group", table_name="sgroups_for_projects")
    op.drop_index("ix_sgroups_for_projects_project", table_name="sgroups_for_projects")
    op.drop_constraint(
        "fk_sgroups_for_projects_project_projects", "sgroups_for_projects", type_="foreignkey"
    )
    op.drop_constraint(
        "fk_sgroups_for_projects_scaling_group_scaling_groups",
        "sgroups_for_projects",
        type_="foreignkey",
    )
    # projects
    op.drop_constraint("uq_projects_name_domain_name", "projects", type_="unique")
    op.drop_index("ix_projects_domain_name", table_name="projects")
    # vfolders
    op.drop_constraint("fk_vfolders_project_id_projects", "vfolders", type_="foreignkey")
    # kernels
    op.drop_constraint("fk_kernels_project_id_projects", "kernels", type_="foreignkey")
    # sessions
    op.drop_constraint("fk_sessions_project_id_projects", "sessions", type_="foreignkey")
    # session_templates
    op.drop_constraint(
        "fk_session_templates_project_id_projects", "session_templates", type_="foreignkey"
    )
    # endpoints
    op.drop_constraint("fk_endpoints_project_id_projects", "endpoints", type_="foreignkey")
    # association_*_users
    op.drop_constraint(
        "fk_association_projects_users_project_id_projects",
        "association_projects_users",
        type_="foreignkey",
    )
    op.drop_constraint(
        "uq_association_user_id_project_id",
        "association_projects_users",
        type_="unique",
    )

    # Rename tables
    op.rename_table("projects", "groups")
    op.rename_table("association_projects_users", "association_groups_users")
    op.rename_table("sgroups_for_projects", "sgroups_for_groups")

    # Alter columns
    op.alter_column("kernels", column_name="project_id", new_column_name="group_id")
    op.alter_column("sessions", column_name="project_id", new_column_name="group_id")
    op.alter_column("session_templates", column_name="project_id", new_column_name="group_id")
    op.alter_column("vfolders", column_name="project_id", new_column_name="group")
    op.alter_column("endpoints", column_name="project_id", new_column_name="project")
    op.alter_column("sgroups_for_groups", column_name="project", new_column_name="group")
    op.alter_column(
        "association_groups_users", column_name="project_id", new_column_name="group_id"
    )

    # Create indexes and constraints
    # sgroups_for_group
    op.create_index("ix_sgroups_for_groups_group", "sgroups_for_groups", ["group"], unique=False)
    op.create_index(
        "ix_sgroups_for_groups_scaling_group", "sgroups_for_groups", ["scaling_group"], unique=False
    )
    op.create_foreign_key(
        op.f("fk_sgroups_for_groups_group_groups"),
        "sgroups_for_groups",
        "groups",
        ["group"],
        ["id"],
        onupdate="CASCADE",
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        op.f("fk_sgroups_for_groups_scaling_group_scaling_groups"),
        "sgroups_for_groups",
        "scaling_groups",
        ["scaling_group"],
        ["name"],
        onupdate="CASCADE",
        ondelete="CASCADE",
    )
    # groups
    op.create_unique_constraint("uq_groups_name_domain_name", "groups", ["name", "domain_name"])
    op.create_index("ix_groups_domain_name", "groups", ["domain_name"], unique=False)
    # vfolders
    op.create_foreign_key(op.f("fk_vfolders_group_groups"), "vfolders", "groups", ["group"], ["id"])
    # kernels
    op.create_foreign_key(
        op.f("fk_kernels_group_id_groups"), "kernels", "groups", ["group_id"], ["id"]
    )
    # sessions
    op.create_foreign_key(
        op.f("fk_sessions_group_id_groups"), "sessions", "groups", ["group_id"], ["id"]
    )
    # session_templates
    op.create_foreign_key(
        op.f("fk_session_templates_group_id_groups"),
        "session_templates",
        "groups",
        ["group_id"],
        ["id"],
    )
    # endpoints
    op.create_foreign_key(
        op.f("fk_endpoints_project_groups"),
        "endpoints",
        "groups",
        ["project"],
        ["id"],
        ondelete="RESTRICT",
    )
    # association_*_users
    op.create_foreign_key(
        op.f("fk_association_groups_users_group_id_groups"),
        "association_groups_users",
        "groups",
        ["group_id"],
        ["id"],
        onupdate="CASCADE",
        ondelete="CASCADE",
    )
    op.create_unique_constraint(
        "uq_association_user_id_group_id", "association_groups_users", ["user_id", "group_id"]
    )

    for n in legacy_names:
        conn.execute(text(f"ALTER TYPE {enum_name} ADD VALUE '{n}';"))
    conn.commit()

    while True:
        vfolder_query = (
            sa.select([vfolders.c.id])
            .select_from(vfolders)
            .where(vfolders.c.ownership_type == VFolderOwnershipType.PROJECT)
            .limit(PAGE_SIZE)
        )

        update_query = (
            sa.update(vfolders)
            .values(ownership_type=LegacyVFolderOwnershipType.GROUP)
            .where(vfolders.c.id.in_(vfolder_query))
        )
        result = conn.execute(update_query)
        if result.rowcount < PAGE_SIZE:
            break

    for n in new_names:
        _delete_enum_value(conn, enum_name, n)
    conn.commit()
    # ### end Alembic commands ###
