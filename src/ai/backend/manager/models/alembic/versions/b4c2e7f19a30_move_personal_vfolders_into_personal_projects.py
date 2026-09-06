"""move personal vfolders into their owners' personal projects

Fills ``vfolders.group`` for user-owned folders with the owner's personal project and
repoints the graph edges a folder created before this change put on the owner's virtual
entity. Ownership is a project from here on, so the column and the graph answer the
same project (BEP-1077 5.1). ``quota_scope_id`` is left alone.

Provisioning the graph for folders that never had edges belongs to the one ownership-data
migration; this one only moves what is already there.

Revision ID: b4c2e7f19a30
Revises: a3f57c4d90e2
Create Date: 2026-09-05 18:00:00

"""

# Part of: NEXT_RELEASE_VERSION

from typing import Final

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "b4c2e7f19a30"
down_revision = "a3f57c4d90e2"
branch_labels = None
depends_on = None

_NAME_IN_PROJECT_INDEX: Final = "uq_vfolders_project_name"

_FILL_PROJECT_COLUMN: Final = sa.text("""
    UPDATE vfolders v
    SET "group" = g.id
    FROM groups g
    WHERE g.type = 'personal'
      AND g.creator_id = v."user"
      AND v.ownership_type = 'user'
      AND v."user" IS NOT NULL
      AND v."group" IS NULL
""")

# The owner's virtual entity paired with the personal project's, for every user-owned
# folder that now names a personal project.
_OWNER_AND_PROJECT_NODES: Final = """
    SELECT uve.id AS user_node, pve.id AS project_node, vve.id AS vfolder_node
    FROM vfolders v
    JOIN virtual_entities vve
      ON vve.entity_type = 'vfolder' AND vve.entity_id = v.id
    JOIN virtual_entities uve
      ON uve.entity_type = 'user' AND uve.entity_id = v."user"
    JOIN virtual_entities pve
      ON pve.entity_type = 'project' AND pve.entity_id = v."group"
    WHERE v.ownership_type = 'user'
      AND v."user" IS NOT NULL
      AND v."group" IS NOT NULL
"""

_ADD_PROJECT_OWN_EDGES: Final = sa.text(f"""
    INSERT INTO entity_memberships (virtual_entity_id, member_entity_id, capped)
    SELECT n.project_node, n.vfolder_node, FALSE
    FROM ({_OWNER_AND_PROJECT_NODES}) n
    JOIN entity_memberships m
      ON m.virtual_entity_id = n.user_node AND m.member_entity_id = n.vfolder_node
    ON CONFLICT (virtual_entity_id, member_entity_id) DO UPDATE SET capped = FALSE
""")

_DROP_OWNER_OWN_EDGES: Final = sa.text(f"""
    DELETE FROM entity_memberships m
    USING ({_OWNER_AND_PROJECT_NODES}) n
    WHERE m.virtual_entity_id = n.user_node AND m.member_entity_id = n.vfolder_node
""")

_ADD_PROJECT_GOVERN_EDGES: Final = sa.text(f"""
    INSERT INTO scope_bindings (virtual_entity_id, scope_entity_id, permission_cap)
    SELECT n.vfolder_node, n.project_node, NULL
    FROM ({_OWNER_AND_PROJECT_NODES}) n
    JOIN scope_bindings b
      ON b.virtual_entity_id = n.vfolder_node AND b.scope_entity_id = n.user_node
    ON CONFLICT DO NOTHING
""")

_DROP_OWNER_GOVERN_EDGES: Final = sa.text(f"""
    DELETE FROM scope_bindings b
    USING ({_OWNER_AND_PROJECT_NODES}) n
    WHERE b.virtual_entity_id = n.vfolder_node AND b.scope_entity_id = n.user_node
""")


_ADD_OWNER_OWN_EDGES: Final = sa.text(f"""
    INSERT INTO entity_memberships (virtual_entity_id, member_entity_id, capped)
    SELECT n.user_node, n.vfolder_node, FALSE
    FROM ({_OWNER_AND_PROJECT_NODES}) n
    JOIN entity_memberships m
      ON m.virtual_entity_id = n.project_node AND m.member_entity_id = n.vfolder_node
    ON CONFLICT (virtual_entity_id, member_entity_id) DO UPDATE SET capped = FALSE
""")

_ADD_OWNER_GOVERN_EDGES: Final = sa.text(f"""
    INSERT INTO scope_bindings (virtual_entity_id, scope_entity_id, permission_cap)
    SELECT n.vfolder_node, n.user_node, NULL
    FROM ({_OWNER_AND_PROJECT_NODES}) n
    JOIN scope_bindings b
      ON b.virtual_entity_id = n.vfolder_node AND b.scope_entity_id = n.project_node
    ON CONFLICT DO NOTHING
""")

_DROP_PROJECT_OWN_EDGES: Final = sa.text(f"""
    DELETE FROM entity_memberships m
    USING ({_OWNER_AND_PROJECT_NODES}) n
    WHERE m.virtual_entity_id = n.project_node AND m.member_entity_id = n.vfolder_node
""")

_DROP_PROJECT_GOVERN_EDGES: Final = sa.text(f"""
    DELETE FROM scope_bindings b
    USING ({_OWNER_AND_PROJECT_NODES}) n
    WHERE b.virtual_entity_id = n.vfolder_node AND b.scope_entity_id = n.project_node
""")

_EMPTY_PROJECT_COLUMN: Final = sa.text("""
    UPDATE vfolders v
    SET "group" = NULL
    FROM groups g
    WHERE g.id = v."group"
      AND g.type = 'personal'
      AND v.ownership_type = 'user'
""")


_DUPLICATE_NAMES_IN_PROJECT: Final = sa.text("""
    SELECT count(*) FROM (
        SELECT 1 FROM vfolders
        WHERE "group" IS NOT NULL
          AND status NOT IN ('delete-complete', 'delete-error')
        GROUP BY "group", name
        HAVING count(*) > 1
    ) AS duplicates
""")


def move_into_personal_projects(conn: sa.Connection) -> None:
    """Fill the project column and repoint the edges. Takes its connection so a test can
    run it against a real database — static analysis does not reach SQL."""
    conn.execute(_FILL_PROJECT_COLUMN)
    conn.execute(_ADD_PROJECT_OWN_EDGES)
    conn.execute(_ADD_PROJECT_GOVERN_EDGES)
    conn.execute(_DROP_OWNER_OWN_EDGES)
    conn.execute(_DROP_OWNER_GOVERN_EDGES)


def name_index_blockers(conn: sa.Connection) -> int:
    """How many (project, name) pairs already stand more than once.

    The unique index cannot be created over them, and which of the folders should keep
    the name is not this migration's to decide.
    """
    return conn.scalar(_DUPLICATE_NAMES_IN_PROJECT) or 0


def move_back_to_owners(conn: sa.Connection) -> None:
    """Put the edges back on the owner and empty the column again.

    A folder whose owner is gone keeps its project: the user row it would go back to is
    not there to name.
    """
    conn.execute(_ADD_OWNER_OWN_EDGES)
    conn.execute(_ADD_OWNER_GOVERN_EDGES)
    conn.execute(_DROP_PROJECT_OWN_EDGES)
    conn.execute(_DROP_PROJECT_GOVERN_EDGES)
    conn.execute(_EMPTY_PROJECT_COLUMN)


def upgrade() -> None:
    conn = op.get_bind()
    move_into_personal_projects(conn)
    blockers = name_index_blockers(conn)
    if blockers:
        raise RuntimeError(
            f"{blockers} project(s) hold more than one live vfolder of the same name. "
            "Rename or purge the duplicates, then run this migration again."
        )
    op.create_index(
        _NAME_IN_PROJECT_INDEX,
        "vfolders",
        ["group", "name"],
        unique=True,
        postgresql_where=sa.text("status NOT IN ('delete-complete', 'delete-error')"),
    )


def downgrade() -> None:
    op.drop_index(_NAME_IN_PROJECT_INDEX, table_name="vfolders")
    move_back_to_owners(op.get_bind())
