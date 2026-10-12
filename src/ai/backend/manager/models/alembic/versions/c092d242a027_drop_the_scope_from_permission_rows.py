"""Drop the scope from permission rows

A role sits in one scope, so its permissions hold there and name no scope of their own.
Removes ``permissions.scope_type`` / ``permissions.scope_id`` with the indexes and the
unique constraint over them, and keys the rows on ``(role_id, entity_type, permission)``.

A row naming a scope other than its role's would lose that scope silently. A folder share
granted the invitee's role rows scoped to the folder; those are dropped first, since the
share is carried from ``vfolder_permissions`` later in the chain. ``3632aad9d5d9`` granted
a session's creator and its project's admins read on that session's app service, scoped to
the session; those are dropped too, since ``f4a1c9d20b73`` retires the entity type and the
session answers for it. So are the rows of a system role ``f4a1c9d20b73`` rewrites or
removes, and the rows scoped to a user, project or domain that no longer exists.

Every other row naming another scope moves to a custom role in that scope, held by the
holders of the role it was on: one new role per ``(role, scope)`` pair, named after the
original, with the status of the original and ``auto_assign`` off. The new role is custom
whether the original is custom or preset-linked, so ``uq_roles_preset_scope`` is not
touched and ``f4a1c9d20b73`` does not rewrite the moved rows. The role is put in the graph
the way ``a7d2c9e41b58`` does it; a scope node that is missing is created, and
``dafe06a6c763`` later gives it its edges. The migration counts the rows still naming
another scope after that and stops when it finds any.

Create Date: 2026-09-09

"""

from __future__ import annotations

import uuid
from collections.abc import Mapping, Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import insert as pg_insert

from ai.backend.manager.models.base import GUID

# revision identifiers, used by Alembic.
revision = "c092d242a027"
down_revision = "c7d419b0a58e"
# Part of: 26.9.0
branch_labels = None
depends_on = None

_CHECK_QUERY = """\
-- permission rows naming a scope other than their role's, per role and scope
SELECT r.id AS role_id, r.name, r.source, r.scope_type AS role_scope_type,
       r.scope_id AS role_scope_id, p.scope_type, p.scope_id, count(*) AS row_count,
       (SELECT count(*) FROM user_roles ur WHERE ur.role_id = r.id) AS holders
FROM permissions p JOIN roles r ON r.id = p.role_id
WHERE p.scope_type IS DISTINCT FROM r.scope_type
   OR p.scope_id IS DISTINCT FROM CAST(r.scope_id AS text)
GROUP BY r.id, r.name, r.source, r.scope_type, r.scope_id, p.scope_type, p.scope_id
ORDER BY r.name, p.scope_type, p.scope_id;"""


def drop_folder_share_grants(conn: sa.engine.Connection) -> None:
    """Drop the rows a folder share granted: scoped to the folder, on a role sitting in
    another scope."""
    conn.execute(
        sa.text("""
            DELETE FROM permissions p
            USING roles r
            WHERE r.id = p.role_id
              AND p.scope_type = 'vfolder'
              AND (p.scope_type IS DISTINCT FROM r.scope_type
                   OR p.scope_id IS DISTINCT FROM CAST(r.scope_id AS text))
        """)
    )


def drop_session_app_service_grants(conn: sa.engine.Connection) -> None:
    """Drop the rows granting read on a session's app service: scoped to the session, on a
    role sitting in another scope."""
    conn.execute(
        sa.text("""
            DELETE FROM permissions p
            USING roles r
            WHERE r.id = p.role_id
              AND p.entity_type = 'session:app_service'
              AND (p.scope_type IS DISTINCT FROM r.scope_type
                   OR p.scope_id IS DISTINCT FROM CAST(r.scope_id AS text))
        """)
    )


# The presets ``f4a1c9d20b73`` writes; it replaces the permissions of the system roles
# linked to them and removes the system roles linked to none.
_REWRITTEN_PRESET_IDS = (
    "9ebf4f57-9e67-5631-997a-d2d79cc3815f",
    "22c4db03-24aa-5ff8-b5a9-64b2a2182413",
    "06057849-3534-546f-b74c-b79d5d3ecf5e",
    "776c1366-dcf3-5abd-b8de-bc3ad3b759ad",
)

_UUID_PATTERN = "^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"


def drop_rewritten_system_role_grants(conn: sa.engine.Connection) -> None:
    """Drop the rows naming another scope on a system role that ``f4a1c9d20b73`` rewrites
    or removes: they do not survive that revision either way."""
    conn.execute(
        sa.text("""
            DELETE FROM permissions p
            USING roles r
            WHERE r.id = p.role_id
              AND r.source = 'system'
              AND (r.role_preset_id IS NULL
                   OR CAST(r.role_preset_id AS text) = ANY(:preset_ids))
              AND (p.scope_type IS DISTINCT FROM r.scope_type
                   OR p.scope_id IS DISTINCT FROM CAST(r.scope_id AS text))
        """).bindparams(preset_ids=list(_REWRITTEN_PRESET_IDS))
    )


def drop_grants_on_deleted_scopes(conn: sa.engine.Connection) -> None:
    """Drop the rows naming another scope that is a user, project or domain no longer in
    the database, or that is not named by a uuid."""
    conn.execute(
        sa.text("""
            DELETE FROM permissions p
            USING roles r
            WHERE r.id = p.role_id
              AND p.scope_type IN ('user', 'project', 'domain')
              AND (p.scope_type IS DISTINCT FROM r.scope_type
                   OR p.scope_id IS DISTINCT FROM CAST(r.scope_id AS text))
              AND (
                  p.scope_id !~* :uuid_pattern
                  OR (p.scope_type = 'user' AND NOT EXISTS (
                      SELECT 1 FROM users u WHERE CAST(u.uuid AS text) = p.scope_id))
                  OR (p.scope_type = 'project' AND NOT EXISTS (
                      SELECT 1 FROM groups g WHERE CAST(g.id AS text) = p.scope_id))
                  OR (p.scope_type = 'domain' AND NOT EXISTS (
                      SELECT 1 FROM domains d WHERE CAST(d.id AS text) = p.scope_id))
              )
        """).bindparams(uuid_pattern=_UUID_PATTERN)
    )


# Metadata local to this revision so that the table snapshots below cannot be altered by
# definitions living in other revisions.
_local_metadata = sa.MetaData()

type _Scope = tuple[str, uuid.UUID]


def _roles_table() -> sa.Table:
    return sa.Table(
        "roles",
        _local_metadata,
        sa.Column("id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v7()")),
        sa.Column("name", sa.String(64), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("source", sa.String(32), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("auto_assign", sa.Boolean, nullable=False),
        sa.Column("role_preset_id", GUID, nullable=True),
        sa.Column("scope_type", sa.String(32), nullable=False),
        sa.Column("scope_id", GUID, nullable=False),
        extend_existing=True,
    )


def _permissions_table() -> sa.Table:
    return sa.Table(
        "permissions",
        _local_metadata,
        sa.Column("role_id", GUID, nullable=False),
        sa.Column("scope_type", sa.String(32), nullable=False),
        sa.Column("scope_id", sa.String(64), nullable=False),
        extend_existing=True,
    )


def _virtual_entities_table() -> sa.Table:
    return sa.Table(
        "virtual_entities",
        _local_metadata,
        sa.Column("id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v7()")),
        sa.Column("entity_type", sa.String(32), nullable=False),
        sa.Column("entity_id", GUID, nullable=False),
        extend_existing=True,
    )


def _entity_memberships_table() -> sa.Table:
    return sa.Table(
        "entity_memberships",
        _local_metadata,
        sa.Column("virtual_entity_id", GUID, nullable=False),
        sa.Column("member_entity_id", GUID, nullable=False),
        sa.Column("capped", sa.Boolean, nullable=False),
        extend_existing=True,
    )


def _scope_bindings_table() -> sa.Table:
    return sa.Table(
        "scope_bindings",
        _local_metadata,
        sa.Column("virtual_entity_id", GUID, nullable=False),
        sa.Column("scope_entity_id", GUID, nullable=False),
        sa.Column("permission_cap", sa.Integer, nullable=True),
        extend_existing=True,
    )


# The pairs of a role and another scope its rows name, in a fixed order. A scope id that
# is not a uuid names no scope a role can sit in; those rows stay for the check below.
_FOREIGN_SCOPE_PAIRS = """
    SELECT r.id AS role_id, r.name, r.description, r.status, p.scope_type, p.scope_id
    FROM permissions p JOIN roles r ON r.id = p.role_id
    WHERE (p.scope_type IS DISTINCT FROM r.scope_type
           OR p.scope_id IS DISTINCT FROM CAST(r.scope_id AS text))
      AND p.scope_id ~* :uuid_pattern
    GROUP BY r.id, r.name, r.description, r.status, p.scope_type, p.scope_id
    ORDER BY r.id, p.scope_type, p.scope_id
    LIMIT :batch_size
"""

_BATCH_SIZE = 100


def move_rows_into_roles_of_their_scope(conn: sa.engine.Connection) -> None:
    """Move each row naming another scope to a custom role in that scope, held by the
    holders of the role the row was on. Works on a batch of pairs at a time; a batch
    moved no longer matches, so the batches run out."""
    query = sa.text(_FOREIGN_SCOPE_PAIRS).bindparams(
        uuid_pattern=_UUID_PATTERN, batch_size=_BATCH_SIZE
    )
    while pairs := conn.execute(query).all():
        role_ids = _create_roles(conn, pairs)
        moves = [
            {
                "b_role_id": role_id,
                "b_original_id": pair.role_id,
                "b_scope_type": pair.scope_type,
                "b_scope_id": pair.scope_id,
            }
            for role_id, pair in zip(role_ids, pairs, strict=True)
        ]
        permissions = _permissions_table()
        conn.execute(
            sa.update(permissions)
            .where(
                permissions.c.role_id == sa.bindparam("b_original_id"),
                permissions.c.scope_type == sa.bindparam("b_scope_type"),
                permissions.c.scope_id == sa.bindparam("b_scope_id"),
            )
            .values(role_id=sa.bindparam("b_role_id")),
            moves,
        )
        conn.execute(
            sa.text("""
                INSERT INTO user_roles (user_id, role_id, granted_by, granted_at)
                SELECT user_id, :b_role_id, granted_by, granted_at
                FROM user_roles WHERE role_id = :b_original_id
                ON CONFLICT (user_id, role_id) DO NOTHING
            """),
            [{k: move[k] for k in ("b_role_id", "b_original_id")} for move in moves],
        )
        _own_roles(
            conn,
            {
                role_id: (pair.scope_type, uuid.UUID(pair.scope_id))
                for role_id, pair in zip(role_ids, pairs, strict=True)
            },
        )


def _create_roles(conn: sa.engine.Connection, pairs: Sequence[sa.Row]) -> Sequence[uuid.UUID]:
    """One custom role per pair, in the scope the pair names, with the name, description
    and status of the pair's role and ``auto_assign`` off. Returns the ids in pair order."""
    roles = _roles_table()
    return [
        conn.execute(
            sa.insert(roles)
            .values(
                name=pair.name,
                description=pair.description,
                source="custom",
                status=pair.status,
                auto_assign=False,
                role_preset_id=None,
                scope_type=pair.scope_type,
                scope_id=uuid.UUID(pair.scope_id),
            )
            .returning(roles.c.id)
        ).scalar_one()
        for pair in pairs
    ]


def _own_roles(conn: sa.engine.Connection, scopes: Mapping[uuid.UUID, _Scope]) -> None:
    """Put each role in the graph as ``a7d2c9e41b58`` does: its node, its own edge and
    binding, and the edge and binding from its scope, whose node is created if missing."""
    nodes = _virtual_entities_table()
    keys: list[_Scope] = [*set(scopes.values())] + [("role", role_id) for role_id in scopes]
    conn.execute(
        pg_insert(nodes)
        .values([{"entity_type": kind, "entity_id": entity_id} for kind, entity_id in keys])
        .on_conflict_do_nothing(index_elements=["entity_type", "entity_id"])
    )
    node_ids: dict[_Scope, uuid.UUID] = {
        (kind, entity_id): node_id
        for kind, entity_id, node_id in conn.execute(
            sa.select(nodes.c.entity_type, nodes.c.entity_id, nodes.c.id).where(
                sa.tuple_(nodes.c.entity_type, nodes.c.entity_id).in_(keys)
            )
        ).all()
    }
    # (role node, scope node) of each role
    owned = [(node_ids[("role", role_id)], node_ids[scope]) for role_id, scope in scopes.items()]
    edges = [
        {"virtual_entity_id": role_node, "member_entity_id": role_node, "capped": False}
        for role_node, _ in owned
    ] + [
        {"virtual_entity_id": scope_node, "member_entity_id": role_node, "capped": False}
        for role_node, scope_node in owned
    ]
    conn.execute(
        pg_insert(_entity_memberships_table())
        .values(edges)
        .on_conflict_do_update(
            index_elements=["virtual_entity_id", "member_entity_id"], set_={"capped": False}
        )
    )
    bindings = [
        {"virtual_entity_id": role_node, "scope_entity_id": role_node, "permission_cap": None}
        for role_node, _ in owned
    ] + [
        {"virtual_entity_id": role_node, "scope_entity_id": scope_node, "permission_cap": None}
        for role_node, scope_node in owned
    ]
    conn.execute(pg_insert(_scope_bindings_table()).values(bindings).on_conflict_do_nothing())


def refuse_rows_disagreeing_with_their_role(conn: sa.engine.Connection) -> None:
    """Stop when a permission row names a scope other than the one its role sits in.

    Dropping the columns would take that scope with them, so the rows are counted while
    they can still be read. After the move above, only a row whose scope id names no
    scope a role can sit in is left; what to do with it is a decision for whoever owns
    the data.

    Once every row agrees with its role, the old unique key — which counts the scope —
    already makes ``(role_id, entity_type, permission)`` unique, so the narrower key the
    upgrade puts in its place needs no deduplication.
    """
    count = conn.execute(
        sa.text("""
            SELECT count(*)
            FROM permissions p JOIN roles r ON r.id = p.role_id
            WHERE p.scope_type IS DISTINCT FROM r.scope_type
               OR p.scope_id IS DISTINCT FROM CAST(r.scope_id AS text)
        """)
    ).scalar_one()
    if count:
        raise RuntimeError(
            f"{count} permission row(s) name a scope other than their role's."
            f" Resolve them first; check query:\n{_CHECK_QUERY}"
        )


def upgrade() -> None:
    conn = op.get_bind()
    drop_folder_share_grants(conn)
    drop_session_app_service_grants(conn)
    drop_rewritten_system_role_grants(conn)
    drop_grants_on_deleted_scopes(conn)
    move_rows_into_roles_of_their_scope(conn)
    refuse_rows_disagreeing_with_their_role(conn)
    op.drop_constraint("uq_permissions_role_scope_entity_permission", "permissions", type_="unique")
    op.drop_index("ix_permissions_role_scope", table_name="permissions")
    op.drop_index("ix_permissions_scope_entity", table_name="permissions")
    op.drop_column("permissions", "scope_id")
    op.drop_column("permissions", "scope_type")
    op.create_index(
        "ix_permissions_entity",
        "permissions",
        ["entity_type"],
        unique=False,
        postgresql_include=["permission", "role_id"],
    )
    op.create_unique_constraint(
        "uq_permissions_role_entity_permission",
        "permissions",
        ["role_id", "entity_type", "permission"],
    )


def downgrade() -> None:
    """Restore the columns and fill them from each row's role.

    The scope a row named before the upgrade is gone; the role's is what the upgrade
    kept, and it is the only scope the row can be given back.
    """
    op.drop_constraint("uq_permissions_role_entity_permission", "permissions", type_="unique")
    op.drop_index("ix_permissions_entity", table_name="permissions")
    op.add_column("permissions", sa.Column("scope_type", sa.String(length=32), nullable=True))
    op.add_column("permissions", sa.Column("scope_id", sa.String(length=64), nullable=True))
    op.execute(
        sa.text("""
            UPDATE permissions p
            SET scope_type = r.scope_type, scope_id = CAST(r.scope_id AS text)
            FROM roles r WHERE r.id = p.role_id
        """)
    )
    op.execute(sa.text("DELETE FROM permissions WHERE scope_type IS NULL OR scope_id IS NULL"))
    op.alter_column("permissions", "scope_type", nullable=False)
    op.alter_column("permissions", "scope_id", nullable=False)
    op.create_index(
        "ix_permissions_role_scope", "permissions", ["role_id", "scope_type", "scope_id"]
    )
    op.create_index(
        "ix_permissions_scope_entity",
        "permissions",
        ["scope_type", "scope_id", "entity_type"],
        postgresql_include=["permission", "role_id"],
    )
    op.create_unique_constraint(
        "uq_permissions_role_scope_entity_permission",
        "permissions",
        ["role_id", "scope_type", "scope_id", "entity_type", "permission"],
    )
