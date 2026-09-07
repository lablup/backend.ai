"""Link roles to the preset they were instantiated from

Adds ``roles.role_preset_id`` and backfills it for existing rows whose name is exactly
what one active preset's naming rule yields for the scope the role is bound to.
A name two presets both yield is left unlinked.

Create Date: 2026-09-08

"""

from __future__ import annotations

import uuid
from collections import defaultdict
from collections.abc import Mapping, Sequence
from typing import Any

import jinja2
import jinja2.sandbox
import sqlalchemy as sa
from alembic import op
from sqlalchemy.engine import Connection

from ai.backend.manager.models.base import GUID

# revision identifiers, used by Alembic.
revision = "b8c828d3636e"
down_revision = "c1a7f3e0d94b"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None

# Metadata local to this revision so that the table snapshots below cannot be
# altered by definitions living in other revisions.
_local_metadata = sa.MetaData()

# Rendered names are stored in ``roles.name`` (sa.String(64)).
_MAX_ROLE_NAME_LENGTH = 64


def _roles_table() -> sa.Table:
    return sa.Table(
        "roles",
        _local_metadata,
        sa.Column("id", GUID, primary_key=True),
        sa.Column("name", sa.String(64), nullable=False),
        sa.Column("source", sa.VARCHAR(16), nullable=False),
        sa.Column("role_preset_id", GUID, nullable=True),
        extend_existing=True,
    )


def _role_presets_table() -> sa.Table:
    return sa.Table(
        "role_presets",
        _local_metadata,
        sa.Column("id", GUID, primary_key=True),
        sa.Column("name", sa.String(64), nullable=False),
        sa.Column("role_name_template", sa.Text, nullable=True),
        sa.Column("scope_type", sa.VARCHAR(32), nullable=False),
        sa.Column("deleted", sa.Boolean, nullable=False),
        extend_existing=True,
    )


def _association_scopes_entities_table() -> sa.Table:
    return sa.Table(
        "association_scopes_entities",
        _local_metadata,
        sa.Column("scope_type", sa.String(32), nullable=False),
        sa.Column("scope_id", sa.String(64), nullable=False),
        sa.Column("entity_type", sa.String(32), nullable=False),
        sa.Column("entity_id", sa.String(64), nullable=False),
        extend_existing=True,
    )


def _virtual_entities_table() -> sa.Table:
    return sa.Table(
        "virtual_entities",
        _local_metadata,
        sa.Column("id", GUID, primary_key=True),
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
        extend_existing=True,
    )


def _scope_table(name: str, id_column: str, name_column: str) -> sa.Table:
    return sa.Table(
        name,
        _local_metadata,
        sa.Column(id_column, GUID, primary_key=True),
        sa.Column(name_column, sa.String(64), nullable=False),
        extend_existing=True,
    )


# Scope type -> (table, id column, name column) of the rows presets instantiate roles on.
_SCOPE_SOURCES: Mapping[str, tuple[str, str, str]] = {
    "domain": ("domains", "id", "name"),
    "project": ("groups", "id", "name"),
    "user": ("users", "uuid", "username"),
}

_template_env = jinja2.sandbox.ImmutableSandboxedEnvironment(undefined=jinja2.StrictUndefined)


def _render_role_name(template: str, scope: Mapping[str, Any]) -> str | None:
    """Minimal copy of V2EntityWriteOps._render_role_name: a migration cannot import
    the repository ops, and the rule must stay frozen at the time of writing."""
    try:
        rendered = _template_env.from_string(template).render(scope=scope).strip()
    except jinja2.TemplateError:
        return None
    if not rendered:
        return None
    return rendered[:_MAX_ROLE_NAME_LENGTH]


def _candidate_names(
    preset_name: str,
    template: str | None,
    scope_type: str,
    scope_id: uuid.UUID,
    scope_name: str,
) -> set[str]:
    """Every name a preset may have given a role on the scope: the legacy rule (the
    preset name as is), the v2 template-less rule (preset name + scope id), and the
    rendered template. The ``{type}-{id}-role`` fallback is not a candidate."""
    suffix = f"-{str(scope_id)[:8]}"
    names = {preset_name, f"{preset_name[: _MAX_ROLE_NAME_LENGTH - len(suffix)]}{suffix}"}
    if template is not None:
        rendered = _render_role_name(
            template, {"id": str(scope_id), "name": scope_name, "type": scope_type}
        )
        if rendered is not None:
            names.add(rendered)
    return names


def _unlinked_system_roles_by_scope(
    conn: Connection, scope_type: str
) -> dict[str, list[tuple[uuid.UUID, str]]]:
    """(role id, name) of every SYSTEM role not yet linked, keyed by the id of the
    scope it is bound to — through the legacy association or the virtual entity graph."""
    roles = _roles_table()
    assoc = _association_scopes_entities_table()
    scope_node = _virtual_entities_table().alias("scope_node")
    role_node = _virtual_entities_table().alias("role_node")
    memberships = _entity_memberships_table()
    unlinked = sa.and_(roles.c.source == "system", roles.c.role_preset_id.is_(None))
    via_association = (
        sa.select(assoc.c.scope_id, roles.c.id, roles.c.name)
        .select_from(assoc.join(roles, assoc.c.entity_id == sa.cast(roles.c.id, sa.String)))
        .where(assoc.c.scope_type == scope_type, assoc.c.entity_type == "role", unlinked)
    )
    via_graph = (
        sa.select(sa.cast(scope_node.c.entity_id, sa.String), roles.c.id, roles.c.name)
        .select_from(
            memberships.join(scope_node, scope_node.c.id == memberships.c.virtual_entity_id)
            .join(role_node, role_node.c.id == memberships.c.member_entity_id)
            .join(roles, roles.c.id == role_node.c.entity_id)
        )
        .where(scope_node.c.entity_type == scope_type, role_node.c.entity_type == "role", unlinked)
    )
    by_scope: dict[str, list[tuple[uuid.UUID, str]]] = defaultdict(list)
    for scope_id, role_id, name in conn.execute(sa.union(via_association, via_graph)).all():
        by_scope[scope_id].append((role_id, name))
    return by_scope


def backfill(conn: Connection) -> None:
    presets_table = _role_presets_table()
    presets = conn.execute(
        sa.select(
            presets_table.c.id,
            presets_table.c.name,
            presets_table.c.role_name_template,
            presets_table.c.scope_type,
        ).where(presets_table.c.deleted.is_(False))
    ).all()
    presets_by_scope_type: dict[str, list[Any]] = defaultdict(list)
    for preset in presets:
        presets_by_scope_type[preset.scope_type].append(preset)

    matches: dict[uuid.UUID, set[uuid.UUID]] = defaultdict(set)
    for scope_type, (table, id_column, name_column) in _SCOPE_SOURCES.items():
        scoped_presets = presets_by_scope_type.get(scope_type)
        if not scoped_presets:
            continue
        roles_by_scope = _unlinked_system_roles_by_scope(conn, scope_type)
        if not roles_by_scope:
            continue
        scope_table = _scope_table(table, id_column, name_column)
        scope_rows = conn.execute(
            sa.select(scope_table.c[id_column], scope_table.c[name_column])
        ).all()
        for scope_id, scope_name in scope_rows:
            scope_roles = roles_by_scope.get(str(scope_id))
            if not scope_roles:
                continue
            for preset in scoped_presets:
                candidates = _candidate_names(
                    preset.name, preset.role_name_template, scope_type, scope_id, scope_name
                )
                for role_id, role_name in scope_roles:
                    if role_name in candidates:
                        matches[role_id].add(preset.id)

    updates: Sequence[dict[str, Any]] = [
        {"b_role_id": role_id, "b_preset_id": next(iter(preset_ids))}
        for role_id, preset_ids in matches.items()
        if len(preset_ids) == 1
    ]
    if not updates:
        return
    roles = _roles_table()
    conn.execute(
        sa.update(roles)
        .where(roles.c.id == sa.bindparam("b_role_id"))
        .values(role_preset_id=sa.bindparam("b_preset_id")),
        updates,
    )


def upgrade() -> None:
    op.add_column("roles", sa.Column("role_preset_id", GUID(), nullable=True))
    op.create_index(op.f("ix_roles_role_preset_id"), "roles", ["role_preset_id"], unique=False)
    op.create_foreign_key(
        "fk_roles_role_preset_id_role_presets",
        "roles",
        "role_presets",
        ["role_preset_id"],
        ["id"],
        ondelete="SET NULL",
    )
    backfill(op.get_bind())


def downgrade() -> None:
    op.drop_constraint("fk_roles_role_preset_id_role_presets", "roles", type_="foreignkey")
    op.drop_index(op.f("ix_roles_role_preset_id"), table_name="roles")
    op.drop_column("roles", "role_preset_id")
