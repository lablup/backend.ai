"""Give a role its own scope

Adds ``roles.scope_type`` / ``roles.scope_id`` (NOT NULL). A role takes the scope most of
its permissions name. A role with no permissions, or whose scope has no virtual entity,
cannot be given one and is removed with everything attached to it. The graph's own edge
of each role is rewritten to match the column.

Create Date: 2026-09-08

"""

from __future__ import annotations

import uuid
from collections import defaultdict
from collections.abc import Mapping, Sequence
from typing import Any

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.engine import Connection

from ai.backend.manager.models.base import GUID

# revision identifiers, used by Alembic.
revision = "a7d2c9e41b58"
down_revision = "b8c828d3636e"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None

# Metadata local to this revision so that the table snapshots below cannot be
# altered by definitions living in other revisions.
_local_metadata = sa.MetaData()

_CHECK_QUERY = """\
-- roles instantiated twice from one preset in one scope
SELECT role_preset_id, scope_type, scope_id, count(*) FROM roles
WHERE role_preset_id IS NOT NULL GROUP BY 1, 2, 3 HAVING count(*) > 1;"""


def _roles_table() -> sa.Table:
    return sa.Table(
        "roles",
        _local_metadata,
        sa.Column("id", GUID, primary_key=True),
        sa.Column("role_preset_id", GUID, nullable=True),
        sa.Column("scope_type", sa.String(32), nullable=True),
        sa.Column("scope_id", GUID, nullable=True),
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


def _object_permissions_table() -> sa.Table:
    return sa.Table(
        "object_permissions",
        _local_metadata,
        sa.Column("role_id", GUID, nullable=False),
        extend_existing=True,
    )


def _association_scopes_entities_table() -> sa.Table:
    return sa.Table(
        "association_scopes_entities",
        _local_metadata,
        sa.Column("entity_type", sa.String(32), nullable=False),
        sa.Column("entity_id", sa.String(64), nullable=False),
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


type _Scope = tuple[str, uuid.UUID]


def _majority_scopes(conn: Connection) -> dict[uuid.UUID, _Scope]:
    """The scope most of each role's permissions name. A scope id that is not a uuid
    cannot name a provisioned scope and does not count."""
    permissions = _permissions_table()
    rows = conn.execute(
        sa.select(
            permissions.c.role_id,
            permissions.c.scope_type,
            permissions.c.scope_id,
            sa.func.count().label("count"),
        ).group_by(permissions.c.role_id, permissions.c.scope_type, permissions.c.scope_id)
    ).all()
    counts: dict[uuid.UUID, dict[_Scope, int]] = defaultdict(dict)
    for role_id, scope_type, scope_id, count in rows:
        try:
            counts[role_id][(scope_type, uuid.UUID(scope_id))] = count
        except ValueError:
            continue
    return {
        role_id: max(scopes, key=lambda scope: (scopes[scope], scope[0], scope[1].int))
        for role_id, scopes in counts.items()
        if scopes
    }


def _nodes(conn: Connection, scopes: set[_Scope]) -> dict[_Scope, uuid.UUID]:
    """The virtual entity of each given scope that has one."""
    if not scopes:
        return {}
    nodes = _virtual_entities_table()
    rows = conn.execute(
        sa.select(nodes.c.entity_type, nodes.c.entity_id, nodes.c.id).where(
            sa.tuple_(nodes.c.entity_type, nodes.c.entity_id).in_(list(scopes))
        )
    ).all()
    return {(entity_type, entity_id): node_id for entity_type, entity_id, node_id in rows}


def _remove_roles(conn: Connection, role_ids: Sequence[uuid.UUID]) -> None:
    """Remove the roles with everything attached: grants and permissions go by FK, the
    rest by hand."""
    if not role_ids:
        return
    ids = list(role_ids)
    ids_text = [str(role_id) for role_id in ids]
    object_permissions = _object_permissions_table()
    conn.execute(sa.delete(object_permissions).where(object_permissions.c.role_id.in_(ids)))
    assoc = _association_scopes_entities_table()
    conn.execute(
        sa.delete(assoc).where(assoc.c.entity_type == "role", assoc.c.entity_id.in_(ids_text))
    )
    nodes = _virtual_entities_table()
    conn.execute(sa.delete(nodes).where(nodes.c.entity_type == "role", nodes.c.entity_id.in_(ids)))
    roles = _roles_table()
    conn.execute(sa.delete(roles).where(roles.c.id.in_(ids)))


def _refuse_preset_duplicates(conn: Connection, assigned: Mapping[uuid.UUID, _Scope]) -> None:
    roles = _roles_table()
    rows = conn.execute(
        sa.select(roles.c.id, roles.c.role_preset_id).where(
            roles.c.id.in_(list(assigned)), roles.c.role_preset_id.is_not(None)
        )
    ).all()
    by_preset_scope: dict[tuple[uuid.UUID, _Scope], list[uuid.UUID]] = defaultdict(list)
    for role_id, preset_id in rows:
        by_preset_scope[(preset_id, assigned[role_id])].append(role_id)
    duplicated = sorted(
        role_id
        for role_ids in by_preset_scope.values()
        if len(role_ids) > 1
        for role_id in role_ids
    )
    if duplicated:
        raise RuntimeError(
            "Roles instantiated twice from one preset in one scope: "
            f"{', '.join(str(role_id) for role_id in duplicated[:20])}"
            f"{' ...' if len(duplicated) > 20 else ''}. Resolve them first; check query:\n"
            f"{_CHECK_QUERY}"
        )


def _own_roles(
    conn: Connection, assigned: Mapping[uuid.UUID, _Scope], scope_nodes: Mapping[_Scope, uuid.UUID]
) -> None:
    """Each scope owns and governs its role in the graph, and nothing else owns it:
    the role's node exists, the edge and binding to its scope exist, and own edges to
    other scopes go."""
    nodes = _virtual_entities_table()
    memberships = _entity_memberships_table()
    bindings = _scope_bindings_table()
    conn.execute(
        pg_insert(nodes)
        .values([{"entity_type": "role", "entity_id": role_id} for role_id in assigned])
        .on_conflict_do_nothing(index_elements=["entity_type", "entity_id"])
    )
    role_nodes = {
        entity_id: node_id
        for entity_id, node_id in conn.execute(
            sa.select(nodes.c.entity_id, nodes.c.id).where(
                nodes.c.entity_type == "role", nodes.c.entity_id.in_(list(assigned))
            )
        ).all()
    }
    edges = [
        {
            "virtual_entity_id": role_nodes[role_id],
            "member_entity_id": role_nodes[role_id],
            "capped": False,
        }
        for role_id in assigned
    ] + [
        {
            "virtual_entity_id": scope_nodes[scope],
            "member_entity_id": role_nodes[role_id],
            "capped": False,
        }
        for role_id, scope in assigned.items()
    ]
    conn.execute(
        pg_insert(memberships)
        .values(edges)
        .on_conflict_do_update(
            index_elements=["virtual_entity_id", "member_entity_id"], set_={"capped": False}
        )
    )
    conn.execute(
        pg_insert(bindings)
        .values(
            [
                {
                    "virtual_entity_id": role_nodes[role_id],
                    "scope_entity_id": role_nodes[role_id],
                    "permission_cap": None,
                }
                for role_id in assigned
            ]
            + [
                {
                    "virtual_entity_id": role_nodes[role_id],
                    "scope_entity_id": scope_nodes[scope],
                    "permission_cap": None,
                }
                for role_id, scope in assigned.items()
            ]
        )
        .on_conflict_do_nothing()
    )
    conn.execute(
        sa.delete(memberships).where(
            memberships.c.member_entity_id == sa.bindparam("b_role_node"),
            memberships.c.virtual_entity_id.not_in([
                sa.bindparam("b_role_node"),
                sa.bindparam("b_scope_node"),
            ]),
            memberships.c.capped.is_(False),
        ),
        [
            {"b_role_node": role_nodes[role_id], "b_scope_node": scope_nodes[scope]}
            for role_id, scope in assigned.items()
        ],
    )


def backfill(conn: Connection) -> None:
    roles = _roles_table()
    role_ids = set(conn.execute(sa.select(roles.c.id)).scalars().all())
    majority = _majority_scopes(conn)
    scope_nodes = _nodes(conn, set(majority.values()))
    assigned = {
        role_id: scope
        for role_id, scope in majority.items()
        if role_id in role_ids and scope in scope_nodes
    }
    _remove_roles(conn, sorted(role_ids - assigned.keys()))
    if not assigned:
        return
    _refuse_preset_duplicates(conn, assigned)
    updates: Sequence[Mapping[str, Any]] = [
        {"b_role_id": role_id, "b_scope_type": scope_type, "b_scope_id": scope_id}
        for role_id, (scope_type, scope_id) in assigned.items()
    ]
    conn.execute(
        sa.update(roles)
        .where(roles.c.id == sa.bindparam("b_role_id"))
        .values(scope_type=sa.bindparam("b_scope_type"), scope_id=sa.bindparam("b_scope_id")),
        updates,
    )
    _own_roles(conn, assigned, scope_nodes)


def upgrade() -> None:
    op.add_column("roles", sa.Column("scope_type", sa.String(length=32), nullable=True))
    op.add_column("roles", sa.Column("scope_id", GUID(), nullable=True))
    backfill(op.get_bind())
    op.alter_column("roles", "scope_type", nullable=False)
    op.alter_column("roles", "scope_id", nullable=False)
    op.create_index("ix_roles_scope", "roles", ["scope_type", "scope_id"], unique=False)
    op.create_index(
        "uq_roles_preset_scope",
        "roles",
        ["role_preset_id", "scope_type", "scope_id"],
        unique=True,
        postgresql_where=sa.text("role_preset_id IS NOT NULL"),
    )
    op.create_foreign_key(
        "fk_roles_scope_virtual_entities",
        "roles",
        "virtual_entities",
        ["scope_type", "scope_id"],
        ["entity_type", "entity_id"],
        ondelete="CASCADE",
        deferrable=True,
        initially="DEFERRED",
    )


def downgrade() -> None:
    op.drop_constraint("fk_roles_scope_virtual_entities", "roles", type_="foreignkey")
    op.drop_index("uq_roles_preset_scope", table_name="roles")
    op.drop_index("ix_roles_scope", table_name="roles")
    op.drop_column("roles", "scope_id")
    op.drop_column("roles", "scope_type")
