"""update endpoint and routing table

Revision ID: 85984c98b90f
Revises: 857bdec5abda
Create Date: 2023-05-11 12:40:09.197522

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from ai.backend.common.types import ClusterMode
from ai.backend.manager.models.base import GUID, URLColumn
from ai.backend.manager.models.routing import RouteStatus

# revision identifiers, used by Alembic.
revision = "85984c98b90f"
down_revision = "857bdec5abda"
branch_labels = None
depends_on = None

routestatus_choices = [v.value for v in RouteStatus]
routestatus = postgresql.ENUM(*routestatus_choices, name="routestatus")


def upgrade():
    routestatus.create(op.get_bind())
    op.add_column(
        "endpoints",
        sa.Column(
            "model_mount_destiation",
            sa.String(length=1024),
            nullable=False,
            default="/models",
            server_default="/models",
        ),
    )
    op.add_column(
        "endpoints",
        sa.Column(
            "created_user", GUID, sa.ForeignKey("users.uuid", ondelete="RESTRICT"), nullable=False
        ),
    )
    op.add_column(
        "endpoints",
        sa.Column(
            "session_owner", GUID, sa.ForeignKey("users.uuid", ondelete="RESTRICT"), nullable=False
        ),
    )
    op.add_column(
        "endpoints",
        sa.Column("tag", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "endpoints",
        sa.Column("startup_command", sa.Text, nullable=True),
    )
    op.add_column(
        "endpoints",
        sa.Column("bootstrap_script", sa.String(length=16 * 1024), nullable=True),
    )
    op.add_column(
        "endpoints",
        sa.Column("callback_url", URLColumn, nullable=True, default=sa.null()),
    )
    op.add_column(
        "endpoints",
        sa.Column("environ", postgresql.JSONB(), nullable=True, default={}),
    )
    op.add_column(
        "endpoints",
        sa.Column("name", sa.String(length=512), nullable=False, unique=True),
    )
    op.add_column(
        "endpoints",
        sa.Column("resource_opts", postgresql.JSONB(), nullable=True, default={}),
    )
    op.add_column(
        "endpoints",
        sa.Column(
            "desired_session_count", sa.Integer, nullable=False, default=0, server_default="0"
        ),
    )
    op.add_column(
        "endpoints",
        sa.Column(
            "cluster_mode",
            sa.String(length=16),
            nullable=False,
            default=ClusterMode.SINGLE_NODE,
            server_default=ClusterMode.SINGLE_NODE.name,
        ),
    )
    op.add_column(
        "endpoints",
        sa.Column("cluster_size", sa.Integer, nullable=False, default=1, server_default="1"),
    )
    op.add_column(
        "endpoints",
        sa.Column(
            "scaling_group",
            sa.String(length=64),
            sa.ForeignKey("scaling_groups.name"),
            nullable=False,
            default="default",
            server_default="default",
        ),
    )
    op.add_column(
        "endpoints", sa.Column("open_to_public", sa.Boolean, default=False, server_default="0")
    )
    op.add_column(
        "routings",
        sa.Column(
            "status",
            sa.Enum(*routestatus_choices, name="routestatus"),
            default="provisioning",
            server_default="provisioning",
            nullable=False,
        ),
    )
    op.add_column(
        "routings",
        sa.Column(
            "session_owner", GUID, sa.ForeignKey("users.uuid", ondelete="RESTRICT"), nullable=False
        ),
    )
    op.add_column(
        "routings",
        sa.Column(
            "domain",
            sa.String(length=64),
            sa.ForeignKey("domains.name", ondelete="RESTRICT"),
            nullable=False,
        ),
    )
    op.add_column(
        "routings",
        sa.Column(
            "project",
            GUID,
            sa.ForeignKey("groups.id", ondelete="RESTRICT"),
            nullable=False,
        ),
    )
    op.add_column(
        "scaling_groups",
        sa.Column(
            "wsproxy_api_token",
            sa.String(length=128),
            nullable=True,
        ),
    )
    op.alter_column("endpoints", "url", nullable=True)


def downgrade():
    op.drop_column("endpoints", "model_mount_destiation")
    op.drop_column("endpoints", "created_user")
    op.drop_column("endpoints", "session_owner")
    op.drop_column("endpoints", "tag")
    op.drop_column("endpoints", "startup_command")
    op.drop_column("endpoints", "bootstrap_script")
    op.drop_column("endpoints", "callback_url")
    op.drop_column("endpoints", "environ")
    op.drop_column("endpoints", "name")
    op.drop_column("endpoints", "resource_opts")
    op.drop_column("endpoints", "desired_session_count")
    op.drop_column("endpoints", "cluster_mode")
    op.drop_column("endpoints", "cluster_size")
    op.drop_column("endpoints", "scaling_group")
    op.drop_column("endpoints", "open_to_public")
    op.drop_column("scaling_groups", "wsproxy_api_token")
    op.alter_column("endpoints", "url", nullable=False)
    op.drop_column("routings", "status")
    op.drop_column("routings", "session_owner")
    op.drop_column("routings", "domain")
    op.drop_column("routings", "project")
    routestatus.drop(op.get_bind())
