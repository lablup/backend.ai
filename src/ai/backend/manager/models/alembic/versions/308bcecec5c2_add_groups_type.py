"""add `groups.type`

Revision ID: 308bcecec5c2
Revises: 8c74e7df26f8
Create Date: 2023-11-30 14:18:59.565099

"""

import enum
from typing import cast
from uuid import UUID, uuid4

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import text

from ai.backend.manager.models.base import GUID, EnumValueType, IDColumn, convention

# revision identifiers, used by Alembic.
revision = "308bcecec5c2"
down_revision = "8c74e7df26f8"
branch_labels = None
depends_on = None

metadata = sa.MetaData(naming_convention=convention)
MAXIMUM_DOTFILE_SIZE = 64 * 1024  # 61 KiB
DEFAULT_PROJECT_RESOURCE_POLICY_NAME = "default"


class ProjectType(enum.StrEnum):
    GENERAL = "general"
    MODEL_STORE = "model-store"


users = sa.Table(
    "users",
    metadata,
    IDColumn("uuid"),
    sa.Column("domain_name", sa.String(length=64), sa.ForeignKey("domains.name"), index=True),
)
groups = sa.Table(
    "groups",
    metadata,
    IDColumn("id"),
    sa.Column("name", sa.String(length=64), nullable=False),
    sa.Column("description", sa.String(length=512)),
    sa.Column("is_active", sa.Boolean, default=True),
    sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    sa.Column(
        "modified_at",
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        onupdate=sa.func.current_timestamp(),
    ),
    #: Field for synchronization with external services.
    sa.Column("integration_id", sa.String(length=512)),
    sa.Column(
        "domain_name",
        sa.String(length=64),
        sa.ForeignKey("domains.name", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
        index=True,
    ),
    # TODO: separate resource-related fields with new domain resource policy table when needed.
    sa.Column("total_resource_slots", JSONB(), default={}),
    sa.Column(
        "allowed_vfolder_hosts",
        JSONB(),
        nullable=False,
        default={},
    ),
    # dotfiles column, \x90 means empty list in msgpack
    sa.Column(
        "dotfiles", sa.LargeBinary(length=MAXIMUM_DOTFILE_SIZE), nullable=False, default=b"\x90"
    ),
    sa.Column(
        "resource_policy",
        sa.String(length=256),
        sa.ForeignKey("project_resource_policies.name"),
        nullable=False,
    ),
    sa.Column(
        "type",
        EnumValueType(ProjectType),
        nullable=False,
        default=ProjectType.GENERAL,
    ),
    sa.UniqueConstraint("name", "domain_name", name="uq_groups_name_domain_name"),
)
association_groups_users = sa.Table(
    "association_groups_users",
    metadata,
    sa.Column(
        "user_id",
        GUID,
        sa.ForeignKey("users.uuid", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
        primary_key=True,
    ),
    sa.Column(
        "group_id",
        GUID,
        sa.ForeignKey("groups.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
        primary_key=True,
    ),
)


projecttype_choices = list(map(str, ProjectType))
projecttype = postgresql.ENUM(
    *projecttype_choices,
    name="projecttype",
)


def upgrade():
    conn = op.get_bind()
    projecttype.create(conn)
    op.add_column(
        "groups",
        sa.Column("type", sa.Enum(*projecttype_choices, name="projecttype"), default="general"),
    )
    conn.execute(text("UPDATE groups SET type = 'general'"))
    op.alter_column("groups", "type", nullable=False)

    domain_names = conn.scalars(text("SELECT name FROM domains")).all()
    domain_names = cast(list[str], domain_names)
    project_resource_policies = conn.scalars(
        text("SELECT name FROM project_resource_policies")
    ).all()
    resource_policy_names = cast(list[str], project_resource_policies)
    try:
        picked_resource_policy = resource_policy_names[0]
    except IndexError:
        conn.execute(
            text(
                f"""INSERT INTO project_resource_policies
                (name, max_vfolder_count, max_quota_scope_size, max_network_count)
                VALUES ('{DEFAULT_PROJECT_RESOURCE_POLICY_NAME}', 0, -1, 3)"""
            )
        )
        picked_resource_policy = DEFAULT_PROJECT_RESOURCE_POLICY_NAME
    for domain_name in domain_names:
        model_store_gid = uuid4()
        conn.execute(
            sa.insert(groups).values({
                "id": model_store_gid,
                "name": "model-store",
                "domain_name": domain_name,
                "resource_policy": picked_resource_policy,
                "type": ProjectType.MODEL_STORE,
            })
        )

        uids = conn.scalars(sa.select(users.c.uuid).where(users.c.domain_name == domain_name)).all()
        uids = cast(list[UUID], uids)
        if uids:
            conn.execute(
                sa.insert(association_groups_users).values(
                    user_id=sa.bindparam("user_id"),
                    group_id=model_store_gid,
                ),
                [{"user_id": uid} for uid in uids],
            )


def downgrade():
    conn = op.get_bind()
    cmd = """DELETE FROM groups WHERE "type" = 'model-store'"""
    conn.execute(text(cmd))
    op.drop_column("groups", "type")
    projecttype.drop(conn)
