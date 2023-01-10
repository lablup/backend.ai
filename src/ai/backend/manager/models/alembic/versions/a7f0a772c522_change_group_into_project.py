"""change_group_into_project

Revision ID: a7f0a772c522
Revises: 213a04e90ecf
Create Date: 2023-01-08 21:53:08.761724

"""
import enum
import textwrap

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import text

from ai.backend.manager.models import VFolderOwnershipType
from ai.backend.manager.models.base import GUID, ResourceSlotColumn, VFolderHostPermissionColumn

# revision identifiers, used by Alembic.
revision = "a7f0a772c522"
down_revision = "213a04e90ecf"
branch_labels = None
depends_on = None


enum_name = VFolderOwnershipType.__name__.lower()


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
    # Create tables
    op.create_table(
        "projects",
        sa.Column(
            "id",
            GUID(),
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("description", sa.String(length=512), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True
        ),
        sa.Column(
            "modified_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("integration_id", sa.String(length=512), nullable=True),
        sa.Column("domain_name", sa.String(length=64), nullable=False),
        sa.Column(
            "total_resource_slots",
            JSONB(),
            nullable=True,
        ),
        sa.Column(
            "allowed_vfolder_hosts",
            JSONB(),
            nullable=False,
        ),
        sa.Column("dotfiles", sa.LargeBinary(length=65536), nullable=False),
        sa.ForeignKeyConstraint(
            ["domain_name"],
            ["domains.name"],
            name=op.f("fk_projects_domain_name_domains"),
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_projects")),
        sa.UniqueConstraint("name", "domain_name", name="uq_projects_name_domain_name"),
    )
    op.create_index(op.f("ix_projects_domain_name"), "projects", ["domain_name"], unique=False)
    op.create_table(
        "association_projects_users",
        sa.Column("user_id", GUID(), nullable=False),
        sa.Column("project_id", GUID(), nullable=False),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            name=op.f("fk_association_projects_users_project_id_projects"),
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.uuid"],
            name=op.f("fk_association_projects_users_user_id_users"),
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("user_id", "project_id", name="uq_association_user_id_project_id"),
    )
    op.create_table(
        "sgroups_for_projects",
        sa.Column("scaling_group", GUID(), nullable=False),
        sa.Column("project", GUID(), nullable=False),
        sa.ForeignKeyConstraint(
            ["project"],
            ["projects.id"],
            name=op.f("fk_sgroups_for_projects_project_projects"),
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["scaling_group"],
            ["scaling_groups.name"],
            name=op.f("fk_sgroups_for_projects_scaling_group_scaling_groups"),
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("scaling_group", "project", name="uq_sgroup_project"),
    )

    # Migrate data

    # remove legacy tables

    op.drop_table("association_groups_users")
    op.drop_index("ix_groups_domain_name", table_name="groups")
    op.drop_table("groups")
    op.add_column("kernels", sa.Column("project_id", GUID(), nullable=False))
    op.drop_constraint("fk_kernels_group_id_groups", "kernels", type_="foreignkey")
    op.create_foreign_key(
        op.f("fk_kernels_project_id_projects"), "kernels", "projects", ["project_id"], ["id"]
    )
    op.drop_column("kernels", "group_id")
    op.add_column(
        "session_templates",
        sa.Column("project_id", GUID(), nullable=True),
    )
    op.drop_constraint(
        "fk_session_templates_group_id_groups", "session_templates", type_="foreignkey"
    )
    op.create_foreign_key(
        op.f("fk_session_templates_project_id_projects"),
        "session_templates",
        "projects",
        ["project_id"],
        ["id"],
    )
    op.drop_column("session_templates", "group_id")
    op.add_column(
        "sgroups_for_groups",
        sa.Column("project", GUID(), nullable=False),
    )
    op.drop_index("ix_sgroups_for_groups_group", table_name="sgroups_for_groups")
    op.drop_constraint("uq_sgroup_ugroup", "sgroups_for_groups", type_="unique")
    op.create_index(
        op.f("ix_sgroups_for_groups_project"), "sgroups_for_groups", ["project"], unique=False
    )
    op.create_unique_constraint(
        "uq_sgroup_project", "sgroups_for_groups", ["scaling_group", "project"]
    )
    op.drop_constraint(
        "fk_sgroups_for_groups_group_groups", "sgroups_for_groups", type_="foreignkey"
    )
    op.create_foreign_key(
        op.f("fk_sgroups_for_groups_project_projects"),
        "sgroups_for_groups",
        "projects",
        ["project"],
        ["id"],
        onupdate="CASCADE",
        ondelete="CASCADE",
    )
    op.drop_column("sgroups_for_groups", "group")
    op.add_column("vfolders", sa.Column("project", GUID(), nullable=True))
    op.drop_constraint("fk_vfolders_group_groups", "vfolders", type_="foreignkey")
    op.create_foreign_key(
        op.f("fk_vfolders_project_projects"), "vfolders", "projects", ["project"], ["id"]
    )
    op.drop_column("vfolders", "group")

    for n in new_names:
        conn.execute(text(f"ALTER TYPE {enum_name} ADD VALUE '{n}';"))
    conn.commit()

    conn.execute(
        text(
            f"UPDATE vfolders SET ownership_type = '{VFolderOwnershipType.PROJECT.value}' WHERE ownership_type = '{LegacyVFolderOwnershipType.GROUP.value}';"
        )
    )

    for n in legacy_names:
        _delete_enum_value(conn, enum_name, n)
    conn.commit()
    # ### end Alembic commands ###


def downgrade():
    conn = op.get_bind()
    # Create tables

    # Migrate data

    # remove legacy tables
    op.add_column(
        "vfolders", sa.Column("group", postgresql.UUID(), autoincrement=False, nullable=True)
    )
    op.drop_constraint(op.f("fk_vfolders_project_projects"), "vfolders", type_="foreignkey")
    op.create_foreign_key("fk_vfolders_group_groups", "vfolders", "groups", ["group"], ["id"])
    op.drop_column("vfolders", "project")
    op.add_column(
        "sgroups_for_groups",
        sa.Column("group", postgresql.UUID(), autoincrement=False, nullable=False),
    )
    op.drop_constraint(
        op.f("fk_sgroups_for_groups_project_projects"), "sgroups_for_groups", type_="foreignkey"
    )
    op.create_foreign_key(
        "fk_sgroups_for_groups_group_groups",
        "sgroups_for_groups",
        "groups",
        ["group"],
        ["id"],
        onupdate="CASCADE",
        ondelete="CASCADE",
    )
    op.drop_constraint("uq_sgroup_project", "sgroups_for_groups", type_="unique")
    op.drop_index(op.f("ix_sgroups_for_groups_project"), table_name="sgroups_for_groups")
    op.create_unique_constraint(
        "uq_sgroup_ugroup", "sgroups_for_groups", ["scaling_group", "group"]
    )
    op.create_index("ix_sgroups_for_groups_group", "sgroups_for_groups", ["group"], unique=False)
    op.drop_column("sgroups_for_groups", "project")
    op.add_column(
        "session_templates",
        sa.Column("group_id", postgresql.UUID(), autoincrement=False, nullable=True),
    )
    op.drop_constraint(
        op.f("fk_session_templates_project_id_projects"), "session_templates", type_="foreignkey"
    )
    op.create_foreign_key(
        "fk_session_templates_group_id_groups", "session_templates", "groups", ["group_id"], ["id"]
    )
    op.drop_column("session_templates", "project_id")
    op.add_column(
        "kernels", sa.Column("group_id", postgresql.UUID(), autoincrement=False, nullable=False)
    )
    op.drop_constraint(op.f("fk_kernels_project_id_projects"), "kernels", type_="foreignkey")
    op.create_foreign_key("fk_kernels_group_id_groups", "kernels", "groups", ["group_id"], ["id"])
    op.drop_column("kernels", "project_id")
    op.create_table(
        "groups",
        sa.Column(
            "id",
            postgresql.UUID(),
            server_default=sa.text("uuid_generate_v4()"),
            autoincrement=False,
            nullable=False,
        ),
        sa.Column("name", sa.VARCHAR(length=64), autoincrement=False, nullable=False),
        sa.Column("description", sa.VARCHAR(length=512), autoincrement=False, nullable=True),
        sa.Column("is_active", sa.BOOLEAN(), autoincrement=False, nullable=True),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            autoincrement=False,
            nullable=True,
        ),
        sa.Column(
            "modified_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            autoincrement=False,
            nullable=True,
        ),
        sa.Column("integration_id", sa.VARCHAR(length=512), autoincrement=False, nullable=True),
        sa.Column("domain_name", sa.VARCHAR(length=64), autoincrement=False, nullable=False),
        sa.Column(
            "total_resource_slots",
            postgresql.JSONB(astext_type=sa.Text()),
            autoincrement=False,
            nullable=True,
        ),
        sa.Column("dotfiles", postgresql.BYTEA(), autoincrement=False, nullable=False),
        sa.Column(
            "allowed_vfolder_hosts",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            autoincrement=False,
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["domain_name"],
            ["domains.name"],
            name="fk_groups_domain_name_domains",
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_groups"),
        sa.UniqueConstraint("name", "domain_name", name="uq_groups_name_domain_name"),
        postgresql_ignore_search_path=False,
    )
    op.create_index("ix_groups_domain_name", "groups", ["domain_name"], unique=False)
    op.create_table(
        "association_groups_users",
        sa.Column("user_id", postgresql.UUID(), autoincrement=False, nullable=False),
        sa.Column("group_id", postgresql.UUID(), autoincrement=False, nullable=False),
        sa.ForeignKeyConstraint(
            ["group_id"],
            ["groups.id"],
            name="fk_association_groups_users_group_id_groups",
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.uuid"],
            name="fk_association_groups_users_user_id_users",
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("user_id", "group_id", name="uq_association_user_id_group_id"),
    )
    op.drop_table("association_projects_users")
    op.drop_index(op.f("ix_projects_domain_name"), table_name="projects")
    op.drop_table("projects")

    for n in legacy_names:
        conn.execute(text(f"ALTER TYPE {enum_name} ADD VALUE '{n}';"))
    conn.commit()

    conn.execute(
        text(
            f"UPDATE vfolders SET ownership_type = '{LegacyVFolderOwnershipType.GROUP.value}' WHERE ownership_type = '{VFolderOwnershipType.PROJECT.value}';"
        )
    )

    for n in new_names:
        _delete_enum_value(conn, enum_name, n)
    conn.commit()
    # ### end Alembic commands ###
