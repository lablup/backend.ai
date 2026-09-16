"""drop vfolder_invitations

Invitations are read and answered through ``entity_shares``: every pending one was
moved there earlier in the chain and the answered ones are history. The graph nodes
of the ``vfolder_invitation`` entity type, the permission rows naming it and the two
enum types only this table used go with it.

Revision ID: a7d0f5b3c841
Revises: f6c9e4a2b730
Create Date: 2026-09-16

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from ai.backend.manager.models.base import GUID

# revision identifiers, used by Alembic.
revision = "a7d0f5b3c841"  # Part of: NEXT_RELEASE_VERSION
down_revision = "f6c9e4a2b730"
branch_labels = None
depends_on = None

_ENTITY_TYPE = "vfolder_invitation"

_DROP_NODE_EDGES = sa.text("""
    DELETE FROM entity_memberships m
    USING virtual_entities ve
    WHERE ve.entity_type = :entity_type
      AND (m.virtual_entity_id = ve.id OR m.member_entity_id = ve.id)
""")

_DROP_NODE_BINDINGS = sa.text("""
    DELETE FROM scope_bindings b
    USING virtual_entities ve
    WHERE ve.entity_type = :entity_type
      AND (b.virtual_entity_id = ve.id OR b.scope_entity_id = ve.id)
""")

_DROP_NODES = sa.text("DELETE FROM virtual_entities WHERE entity_type = :entity_type")

_DROP_PERMISSIONS = sa.text("DELETE FROM permissions WHERE entity_type = :entity_type")


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(_DROP_NODE_EDGES, {"entity_type": _ENTITY_TYPE})
    conn.execute(_DROP_NODE_BINDINGS, {"entity_type": _ENTITY_TYPE})
    conn.execute(_DROP_NODES, {"entity_type": _ENTITY_TYPE})
    conn.execute(_DROP_PERMISSIONS, {"entity_type": _ENTITY_TYPE})
    op.drop_table("vfolder_invitations")
    op.execute("DROP TYPE IF EXISTS vfolderinvitationstate")
    op.execute("DROP TYPE IF EXISTS vfoldermountpermission")


def downgrade() -> None:
    # The rows are not restored: the shares carry the invitations.
    mount_permission = postgresql.ENUM(
        "ro", "rw", "wd", name="vfoldermountpermission", create_type=False
    )
    state = postgresql.ENUM(
        "pending",
        "canceled",
        "accepted",
        "rejected",
        name="vfolderinvitationstate",
        create_type=False,
    )
    mount_permission.create(op.get_bind(), checkfirst=True)
    state.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "vfolder_invitations",
        sa.Column("id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v7()")),
        sa.Column("permission", mount_permission, nullable=True),
        sa.Column("inviter", sa.String(length=256), nullable=True),
        sa.Column("invitee", sa.String(length=256), nullable=False),
        sa.Column("state", state, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "vfolder",
            GUID,
            sa.ForeignKey("vfolders.id", onupdate="CASCADE", ondelete="CASCADE"),
            nullable=False,
        ),
    )
