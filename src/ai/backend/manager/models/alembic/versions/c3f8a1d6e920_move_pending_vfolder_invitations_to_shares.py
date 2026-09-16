"""move pending vfolder invitations to entity_shares

Invitations are read and answered through ``entity_shares`` now, so an invitation still
waiting in ``vfolder_invitations`` would never show up. Each pending one becomes a
pending share; answered ones are history and stay behind. ``vfolder_invitations``
itself is left in place.

A share names its folder by the folder's graph node, so a folder with a waiting
invitation and no node is given one, owned and governed by its project.

Revision ID: c3f8a1d6e920
Revises: e8b1d4a7c2f9
Create Date: 2026-09-15

"""

from __future__ import annotations

from typing import Final

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "c3f8a1d6e920"  # Part of: NEXT_RELEASE_VERSION
down_revision = "e8b1d4a7c2f9"
branch_labels = None
depends_on = None

_PENDING_FOLDERS: Final = """
    SELECT DISTINCT v.id, v."group"
    FROM vfolder_invitations i
    JOIN vfolders v ON v.id = i.vfolder
    WHERE i.state = 'pending'
"""

_ADD_FOLDER_NODES: Final = sa.text(f"""
    INSERT INTO virtual_entities (entity_type, entity_id)
    SELECT 'vfolder', f.id FROM ({_PENDING_FOLDERS}) f
    ON CONFLICT (entity_type, entity_id) DO NOTHING
""")

# A node owns and governs itself, the way a created entity's does.
_ADD_SELF_MEMBERSHIPS: Final = sa.text("""
    INSERT INTO entity_memberships (virtual_entity_id, member_entity_id, capped)
    SELECT id, id, FALSE FROM virtual_entities
    WHERE entity_type IN ('vfolder', 'entity_share')
    ON CONFLICT (virtual_entity_id, member_entity_id) DO NOTHING
""")

_ADD_SELF_BINDINGS: Final = sa.text("""
    INSERT INTO scope_bindings (virtual_entity_id, scope_entity_id, permission_cap)
    SELECT id, id, NULL FROM virtual_entities
    WHERE entity_type IN ('vfolder', 'entity_share')
    ON CONFLICT DO NOTHING
""")

_FOLDER_AND_PROJECT_NODES: Final = f"""
    SELECT folder_node.id AS folder_node, project_node.id AS project_node
    FROM ({_PENDING_FOLDERS}) f
    JOIN virtual_entities folder_node
      ON folder_node.entity_type = 'vfolder' AND folder_node.entity_id = f.id
    JOIN virtual_entities project_node
      ON project_node.entity_type = 'project' AND project_node.entity_id = f."group"
"""

_ADD_FOLDER_OWN_EDGES: Final = sa.text(f"""
    INSERT INTO entity_memberships (virtual_entity_id, member_entity_id, capped)
    SELECT n.project_node, n.folder_node, FALSE FROM ({_FOLDER_AND_PROJECT_NODES}) n
    ON CONFLICT (virtual_entity_id, member_entity_id) DO NOTHING
""")

_ADD_FOLDER_GOVERN_EDGES: Final = sa.text(f"""
    INSERT INTO scope_bindings (virtual_entity_id, scope_entity_id, permission_cap)
    SELECT n.folder_node, n.project_node, NULL FROM ({_FOLDER_AND_PROJECT_NODES}) n
    ON CONFLICT DO NOTHING
""")

# The latest waiting invitation per folder and address stands; one live share holds a
# pair. ``wd`` lends what ``rw`` does (BEP-1077 5.7): READ | UPDATE | SOFT_DELETE.
_ADD_SHARES: Final = sa.text("""
    INSERT INTO entity_shares (
        sharer_user_id, recipient_email, target_entity_type, target_entity_id,
        permission_cap, status, created_at, updated_at
    )
    SELECT DISTINCT ON (i.vfolder, i.invitee)
        u.uuid,
        i.invitee,
        'vfolder',
        i.vfolder,
        CASE WHEN i.permission = 'ro' THEN 1 ELSE 11 END,
        'pending',
        i.created_at,
        i.updated_at
    FROM vfolder_invitations i
    JOIN virtual_entities node ON node.entity_type = 'vfolder' AND node.entity_id = i.vfolder
    LEFT JOIN users u ON u.email = i.inviter
    WHERE i.state = 'pending'
      AND char_length(i.invitee) <= 64
      AND NOT EXISTS (
        SELECT 1 FROM entity_shares s
        WHERE s.target_entity_type = 'vfolder'
          AND s.target_entity_id = i.vfolder
          AND s.recipient_email = i.invitee
          AND s.status IN ('pending', 'accepted')
      )
    ORDER BY i.vfolder, i.invitee, i.updated_at DESC
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


def move_pending_invitations_to_shares(conn: sa.Connection) -> None:
    conn.execute(_ADD_FOLDER_NODES)
    conn.execute(_ADD_FOLDER_OWN_EDGES)
    conn.execute(_ADD_FOLDER_GOVERN_EDGES)
    conn.execute(_ADD_SHARES)
    conn.execute(_ADD_SHARE_NODES)
    conn.execute(_ADD_SELF_MEMBERSHIPS)
    conn.execute(_ADD_SELF_BINDINGS)
    conn.execute(_ADD_SHARE_OWN_EDGES)
    conn.execute(_ADD_SHARE_GOVERN_EDGES)


def upgrade() -> None:
    move_pending_invitations_to_shares(op.get_bind())


def downgrade() -> None:
    # The source rows were never removed, and a share written after this revision
    # cannot be told apart from one moved here, so nothing is taken back.
    pass
