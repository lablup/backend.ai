"""Backfill public membership

Every type the `public_member` role grants READ on has to be registered in `public`
for an id read to pass. Put the rows on file there: the whole of the seven types that
are public as a type, and the rows of container registry, image and resource preset
whose column says so.

`container_registries.is_global` decides registration, so it is settled first: the rows
left NULL become false, which is what every read has taken NULL to mean, and the column
turns NOT NULL. Its default stays true, so a registry created without the value is still
global.

Revision ID: f1c47b92e3a6
Revises: c4a71e0d5b38
Create Date: 2026-09-21

"""

from __future__ import annotations

from typing import Final

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "f1c47b92e3a6"  # Part of: NEXT_RELEASE_VERSION
down_revision = "c4a71e0d5b38"
branch_labels = None
depends_on = None

CHUNK_SIZE: Final[int] = 1000

_PUBLIC_NODE: Final[str] = """
    SELECT ve.id FROM virtual_entities ve
    JOIN global_entities ge ON ve.entity_type = 'global' AND ve.entity_id = ge.id
    WHERE ge.name = 'public'
"""

# The nodes of one page of rows. A row without a node names none.
_NODES: Final[str] = """
    SELECT ve.id FROM virtual_entities ve
    WHERE ve.entity_type = :entity_type
      AND ve.entity_id = ANY(CAST(:entity_ids AS uuid[]))
"""

_ADD_MEMBERSHIPS: Final = sa.text(f"""
    INSERT INTO entity_memberships (virtual_entity_id, member_entity_id, capped)
    SELECT p.id, n.id, FALSE FROM ({_PUBLIC_NODE}) p, ({_NODES}) n
    ON CONFLICT (virtual_entity_id, member_entity_id) DO NOTHING
""")

_ADD_BINDINGS: Final = sa.text(f"""
    INSERT INTO scope_bindings (virtual_entity_id, scope_entity_id, permission_cap)
    SELECT n.id, p.id, NULL FROM ({_PUBLIC_NODE}) p, ({_NODES}) n
    ON CONFLICT DO NOTHING
""")

_REMOVE_MEMBERSHIPS: Final = sa.text(f"""
    DELETE FROM entity_memberships em
    USING ({_PUBLIC_NODE}) p, ({_NODES}) n
    WHERE em.virtual_entity_id = p.id
      AND em.member_entity_id = n.id
      AND em.capped IS FALSE
""")

_REMOVE_BINDINGS: Final = sa.text(f"""
    DELETE FROM scope_bindings sb
    USING ({_PUBLIC_NODE}) p, ({_NODES}) n
    WHERE sb.virtual_entity_id = n.id
      AND sb.scope_entity_id = p.id
      AND sb.permission_cap IS NULL
""")


class _Source:
    """The rows of one table that belong in `public`, paged by the column naming the
    entity. ``where`` is the condition a row meets to belong there, and is empty where
    the whole table does.

    A plain class rather than a dataclass: alembic loads a revision without putting it
    in `sys.modules`, and `@dataclass` reads the module's namespace to resolve its
    annotations."""

    entity_type: str
    table: str
    id_column: str
    where: str
    joins: str

    def __init__(
        self,
        entity_type: str,
        table: str,
        id_column: str,
        where: str = "",
        joins: str = "",
    ) -> None:
        self.entity_type = entity_type
        self.table = table
        self.id_column = id_column
        self.where = where
        self.joins = joins

    def page(self) -> sa.TextClause:
        conditions = [f"({self.where})"] if self.where else []
        conditions.append(
            f"(CAST(:after AS uuid) IS NULL OR {self.table}.{self.id_column} > CAST(:after AS uuid))"
        )
        return sa.text(f"""
            SELECT {self.table}.{self.id_column} AS entity_id
            FROM {self.table} {self.joins}
            WHERE {" AND ".join(conditions)}
            ORDER BY {self.table}.{self.id_column}
            LIMIT :limit
        """)


_SETTLE_IS_GLOBAL: Final = sa.text("""
    UPDATE container_registries SET is_global = FALSE WHERE is_global IS NULL
""")


# The seven types every user reads in whole, then the three switched per row. A
# container registry reads as public when `is_global` says so, an image when the
# registry it was scanned from does, a resource preset when it is bound to no
# resource group.
SOURCES: Final[tuple[_Source, ...]] = (
    _Source("runtime_variant", "runtime_variants", "id"),
    _Source("runtime_variant_preset", "runtime_variant_presets", "id"),
    _Source("prometheus_query_preset", "prometheus_query_presets", "id"),
    _Source("prometheus_query_preset_category", "prometheus_query_preset_categories", "id"),
    _Source("resource_slot_type", "resource_slot_types", "uuid"),
    _Source("login_client_type", "login_client_types", "id"),
    _Source("deployment_preset", "deployment_revision_presets", "id"),
    _Source(
        "container_registry",
        "container_registries",
        "id",
        where="container_registries.is_global",
    ),
    _Source(
        "image",
        "images",
        "id",
        where="registry.is_global",
        joins="JOIN container_registries registry ON registry.id = images.registry_id",
    ),
    _Source(
        "resource_preset",
        "resource_presets",
        "id",
        where="resource_presets.scaling_group_name IS NULL",
    ),
)


def _for_each_chunk(conn: sa.Connection, statements: tuple[sa.TextClause, ...]) -> None:
    for source in SOURCES:
        page = source.page()
        after = None
        while True:
            entity_ids = conn.execute(page, {"after": after, "limit": CHUNK_SIZE}).scalars().all()
            if not entity_ids:
                break
            params = {"entity_type": source.entity_type, "entity_ids": list(entity_ids)}
            for statement in statements:
                conn.execute(statement, params)
            after = entity_ids[-1]


def settle_is_global(conn: sa.Connection) -> None:
    """A registry left NULL becomes not global, which is what every read has taken NULL
    to mean. Run before the backfill, so the column it reads has an answer for
    every row."""
    conn.execute(_SETTLE_IS_GLOBAL)


def add_public_edges(conn: sa.Connection) -> None:
    _for_each_chunk(conn, (_ADD_MEMBERSHIPS, _ADD_BINDINGS))


def remove_public_edges(conn: sa.Connection) -> None:
    _for_each_chunk(conn, (_REMOVE_MEMBERSHIPS, _REMOVE_BINDINGS))


def upgrade() -> None:
    conn = op.get_bind()
    settle_is_global(conn)
    op.alter_column(
        "container_registries",
        "is_global",
        existing_type=sa.Boolean(),
        nullable=False,
        existing_server_default="true",
    )
    add_public_edges(conn)


def downgrade() -> None:
    remove_public_edges(op.get_bind())
    op.alter_column(
        "container_registries",
        "is_global",
        existing_type=sa.Boolean(),
        nullable=True,
        existing_server_default="true",
    )
