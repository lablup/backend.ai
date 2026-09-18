"""add vfolder_user_mount_policies

The mount level one user gets on a folder, set by whoever may update the folder. It
replaces the legacy ``vfolder_permissions`` row the mount path read, so every legacy
row is copied over: ``wd`` folds to ``rw``, the widest of duplicate rows wins, and a
personal folder's owner needs no row. The maker of a model store folder keeps the
read-write mount the folder's ``ro`` default takes from everyone else.

A legacy row also records an accepted share, which the share records did not carry
before: an accepted ``entity_shares`` row is written for each, with the graph nodes
the row references. Whether the recipient's share edge exists is left to the ownership
backfill.

Revision ID: e5b8d3f0a129
Revises: d4a7c2e9f018
Create Date: 2026-09-16

"""

from __future__ import annotations

from typing import Final

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID

# revision identifiers, used by Alembic.
revision = "e5b8d3f0a129"  # Part of: NEXT_RELEASE_VERSION
down_revision = "d4a7c2e9f018"
branch_labels = None
depends_on = None

# A legacy row on a folder the user does not own. ``wd`` and NULL read as ``rw``.
_LEGACY_ROWS: Final = """
    SELECT p.vfolder, p."user", v."user" AS owner,
           CASE WHEN p.permission = 'ro' THEN 'ro' ELSE 'rw' END AS permission
    FROM vfolder_permissions p
    JOIN vfolders v ON v.id = p.vfolder
    WHERE v."user" IS DISTINCT FROM p."user"
"""

_ADD_MODEL_STORE_CREATOR_POLICIES: Final = sa.text("""
    INSERT INTO vfolder_user_mount_policies (vfolder_id, user_id, permission)
    SELECT v.id, v.creator_id, 'rw'
    FROM vfolders v
    JOIN groups g ON g.id = v."group"
    JOIN users u ON u.uuid = v.creator_id
    WHERE g.type = 'model-store' AND v.ownership_type = 'group'
    ON CONFLICT (vfolder_id, user_id) DO NOTHING
""")

_COPY_LEGACY_POLICIES: Final = sa.text(f"""
    INSERT INTO vfolder_user_mount_policies (vfolder_id, user_id, permission)
    SELECT DISTINCT ON (r.vfolder, r."user") r.vfolder, r."user", r.permission
    FROM ({_LEGACY_ROWS}) r
    ORDER BY r.vfolder, r."user", CASE WHEN r.permission = 'rw' THEN 0 ELSE 1 END
    ON CONFLICT (vfolder_id, user_id) DO NOTHING
""")

_ADD_FOLDER_NODES: Final = sa.text(f"""
    INSERT INTO virtual_entities (entity_type, entity_id)
    SELECT DISTINCT 'vfolder', r.vfolder FROM ({_LEGACY_ROWS}) r
    ON CONFLICT (entity_type, entity_id) DO NOTHING
""")

_ADD_USER_NODES: Final = sa.text(f"""
    INSERT INTO virtual_entities (entity_type, entity_id)
    SELECT DISTINCT 'user', r."user" FROM ({_LEGACY_ROWS}) r
    ON CONFLICT (entity_type, entity_id) DO NOTHING
""")

# ``rw`` lends what ``wd`` does (BEP-1077 5.7): READ | UPDATE | SOFT_DELETE.
_ADD_ACCEPTED_SHARES: Final = sa.text(f"""
    INSERT INTO entity_shares (
        sharer_user_id, recipient_entity_type, recipient_entity_id,
        target_entity_type, target_entity_id, permission_cap, status
    )
    SELECT DISTINCT ON (r.vfolder, r."user")
        r.owner, 'user', r."user", 'vfolder', r.vfolder,
        CASE WHEN r.permission = 'ro' THEN 1 ELSE 11 END, 'accepted'
    FROM ({_LEGACY_ROWS}) r
    WHERE NOT EXISTS (
        SELECT 1 FROM entity_shares s
        WHERE s.target_entity_type = 'vfolder'
          AND s.target_entity_id = r.vfolder
          AND s.recipient_entity_type = 'user'
          AND s.recipient_entity_id = r."user"
          AND s.status = 'accepted'
    )
    ORDER BY r.vfolder, r."user", CASE WHEN r.permission = 'rw' THEN 0 ELSE 1 END
""")

_SHARES_WITHOUT_A_NODE: Final = """
    SELECT s.id, s.target_entity_id
    FROM entity_shares s
    WHERE s.target_entity_type = 'vfolder'
      AND NOT EXISTS (
        SELECT 1 FROM virtual_entities ve
        WHERE ve.entity_type = 'entity_share' AND ve.entity_id = s.id
      )
"""

_ADD_SHARE_NODES: Final = sa.text(f"""
    INSERT INTO virtual_entities (entity_type, entity_id)
    SELECT 'entity_share', s.id FROM ({_SHARES_WITHOUT_A_NODE}) s
    ON CONFLICT (entity_type, entity_id) DO NOTHING
""")

# A node owns and governs itself, the way a created entity's does.
_ADD_SELF_MEMBERSHIPS: Final = sa.text("""
    INSERT INTO entity_memberships (virtual_entity_id, member_entity_id, capped)
    SELECT id, id, FALSE FROM virtual_entities
    WHERE entity_type IN ('user', 'vfolder', 'entity_share')
    ON CONFLICT (virtual_entity_id, member_entity_id) DO NOTHING
""")

_ADD_SELF_BINDINGS: Final = sa.text("""
    INSERT INTO scope_bindings (virtual_entity_id, scope_entity_id, permission_cap)
    SELECT id, id, NULL FROM virtual_entities
    WHERE entity_type IN ('user', 'vfolder', 'entity_share')
    ON CONFLICT DO NOTHING
""")

_SHARE_AND_FOLDER_NODES: Final = """
    SELECT share_node.id AS share_node, folder_node.id AS folder_node
    FROM entity_shares s
    JOIN virtual_entities share_node
      ON share_node.entity_type = 'entity_share' AND share_node.entity_id = s.id
    JOIN virtual_entities folder_node
      ON folder_node.entity_type = 'vfolder' AND folder_node.entity_id = s.target_entity_id
    WHERE s.target_entity_type = 'vfolder'
"""

_ADD_SHARE_OWN_EDGES: Final = sa.text(f"""
    INSERT INTO entity_memberships (virtual_entity_id, member_entity_id, capped)
    SELECT n.folder_node, n.share_node, FALSE FROM ({_SHARE_AND_FOLDER_NODES}) n
    ON CONFLICT (virtual_entity_id, member_entity_id) DO NOTHING
""")

_ADD_SHARE_GOVERN_EDGES: Final = sa.text(f"""
    INSERT INTO scope_bindings (virtual_entity_id, scope_entity_id, permission_cap)
    SELECT n.share_node, n.folder_node, NULL FROM ({_SHARE_AND_FOLDER_NODES}) n
    ON CONFLICT DO NOTHING
""")


def copy_legacy_mount_rows(conn: sa.Connection) -> None:
    conn.execute(_ADD_MODEL_STORE_CREATOR_POLICIES)
    conn.execute(_COPY_LEGACY_POLICIES)
    conn.execute(_ADD_FOLDER_NODES)
    conn.execute(_ADD_USER_NODES)
    conn.execute(_ADD_ACCEPTED_SHARES)
    conn.execute(_ADD_SHARE_NODES)
    conn.execute(_ADD_SELF_MEMBERSHIPS)
    conn.execute(_ADD_SELF_BINDINGS)
    conn.execute(_ADD_SHARE_OWN_EDGES)
    conn.execute(_ADD_SHARE_GOVERN_EDGES)


def upgrade() -> None:
    op.create_table(
        "vfolder_user_mount_policies",
        sa.Column("id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v7()")),
        sa.Column(
            "vfolder_id",
            GUID,
            sa.ForeignKey("vfolders.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            GUID,
            sa.ForeignKey("users.uuid", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("permission", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("vfolder_id", "user_id"),
    )
    copy_legacy_mount_rows(op.get_bind())


def downgrade() -> None:
    # The legacy rows were never removed, and a share written after this revision
    # cannot be told apart from one written here, so only the table goes.
    op.drop_table("vfolder_user_mount_policies")
