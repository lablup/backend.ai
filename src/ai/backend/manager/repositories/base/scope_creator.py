"""Composite spec for race-free scope provisioning.

A scope-creator spec coordinates the inserts that together provision a new RBAC
scope: the scope row itself (domain, project, ...), any parent-scope mapping
rows, and roles + role-scope associations + permissions instantiated from each
active role preset matching the scope type.

``ScopeCreator`` extends :class:`Creator`: its inherited ``spec`` builds the scope
row (so the insert is delegated to ``execute_creator``), while ``scope_spec`` (a
:class:`ScopeCreatorSpec`) supplies the scope-extension hooks. Orchestration of the
surrounding RBAC rows lives in :func:`execute_scope_creator`.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING
from uuid import UUID

import sqlalchemy as sa

from ai.backend.common.data.permission.types import EntityType, RBACElementType, RelationType
from ai.backend.common.identifier.role_preset import RolePresetID
from ai.backend.manager.models.base import Base
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.rbac_models.role_permission_preset import (
    RolePermissionPresetRow,
)
from ai.backend.manager.models.rbac_models.role_preset import RolePresetRow

from .creator import BulkCreator, Creator, CreatorSpec, execute_bulk_creator, execute_creator

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession as SASession


@dataclass(frozen=True)
class ScopeContext:
    """Locator for a scope row.

    Carries the ``(scope_type, scope_id)`` pair used by downstream RBAC tables
    (``permissions``, ``association_scopes_entities``) to reference the scope.
    """

    scope_type: RBACElementType
    scope_id: str


class ScopeCreatorSpec[TScopeRow: Base](ABC):
    """Scope-extension hooks for a scope type.

    Subclass per scope type (e.g. ``DomainScopeCreatorSpec``,
    ``ProjectScopeCreatorSpec``). Owns no table and does not build the scope row; it
    derives the new scope's context and declares its pre-existing parent scope(s).
    """

    @abstractmethod
    def extract_scope_context(self, scope_row: TScopeRow) -> ScopeContext:
        """Derive ``(scope_type, scope_id)`` from the just-inserted scope row.

        The orchestrator uses this to look up matching role presets and to populate
        ``scope_id`` on derived permission and association rows.
        """
        raise NotImplementedError

    @abstractmethod
    def parent_scopes(self) -> Iterable[ScopeContext]:
        """Pre-existing parent scope(s) the new scope should be mapped under.

        Held by this spec (set at construction), independent of the new scope. The
        orchestrator builds one parent-to-new-scope association row per returned
        scope.
        """
        raise NotImplementedError


@dataclass
class ScopeCreator[TScopeRow: Base](Creator[TScopeRow]):
    """Bundles the scope-row creator spec and its scope hooks for
    :func:`execute_scope_creator`.

    Extends :class:`Creator`: the inherited ``spec`` builds the scope row (insert
    delegated to ``execute_creator``); ``scope_spec`` supplies the scope-extension
    hooks.
    """

    scope_spec: ScopeCreatorSpec[TScopeRow]


@dataclass
class ScopeCreatorResult[TScopeRow: Base]:
    """Outcome of a successful scope provisioning.

    Only surfaces the freshly-inserted scope row and the roles that were
    instantiated from active role presets. Auxiliary rows (permissions,
    role-to-scope associations, parent-scope associations) are still
    inserted by the orchestrator but are not returned.
    """

    scope_row: TScopeRow
    role_rows: list[RoleRow]


@dataclass(frozen=True)
class _RoleCreatorSpec(CreatorSpec[RoleRow]):
    """Insert a role row as a shallow snapshot of a role preset."""

    name: str

    def build_row(self) -> RoleRow:
        return RoleRow(name=self.name)


@dataclass(frozen=True)
class _PresetPermissionCreatorSpec(CreatorSpec[PermissionRow]):
    """Insert a permission row snapshotted from a ``role_permission_presets`` entry.

    Built after the owning role row has been flushed, so ``role_id`` is known.
    """

    scope_context: ScopeContext
    role_id: UUID
    permission_preset: RolePermissionPresetRow

    def build_row(self) -> PermissionRow:
        return PermissionRow(
            role_id=self.role_id,
            scope_type=self.scope_context.scope_type.to_scope_type(),
            scope_id=self.scope_context.scope_id,
            entity_type=self.permission_preset.entity_type,
            operation=self.permission_preset.operation,
        )


@dataclass(frozen=True)
class _RoleScopeAssociationSpec(CreatorSpec[AssociationScopesEntitiesRow]):
    """Insert the association_scopes_entities row tying a role to its scope."""

    role_id: UUID
    scope_context: ScopeContext

    def build_row(self) -> AssociationScopesEntitiesRow:
        return AssociationScopesEntitiesRow(
            scope_type=self.scope_context.scope_type.to_scope_type(),
            scope_id=self.scope_context.scope_id,
            entity_type=EntityType.ROLE,
            entity_id=str(self.role_id),
            relation_type=RelationType.AUTO,
        )


@dataclass(frozen=True)
class _ParentScopeAssociationSpec(CreatorSpec[AssociationScopesEntitiesRow]):
    """Insert the association_scopes_entities row tying a scope to its parent scope."""

    child_scope_context: ScopeContext
    parent_scope_context: ScopeContext

    def build_row(self) -> AssociationScopesEntitiesRow:
        return AssociationScopesEntitiesRow(
            scope_type=self.parent_scope_context.scope_type.to_scope_type(),
            scope_id=self.parent_scope_context.scope_id,
            entity_type=self.child_scope_context.scope_type.to_entity_type(),
            entity_id=self.child_scope_context.scope_id,
            relation_type=RelationType.AUTO,
        )


@dataclass(frozen=True)
class _PresetRoleGroup:
    """An active role preset with its permission preset entries, grouped per preset."""

    role_name: str
    permission_presets: list[RolePermissionPresetRow] = field(default_factory=list)


async def _collect_preset_groups(
    db_sess: SASession,
    scope_context: ScopeContext,
) -> list[_PresetRoleGroup]:
    """Fetch active role presets matching the scope, grouped with their permissions.

    One ``LEFT OUTER JOIN`` between ``role_presets`` and ``role_permission_presets``
    is issued; the returned ``(preset, permission_preset_or_None)`` rows are grouped
    by preset id in Python.
    """
    rows = await db_sess.execute(
        sa.select(RolePresetRow, RolePermissionPresetRow)
        .select_from(RolePresetRow)
        .outerjoin(
            RolePermissionPresetRow,
            RolePermissionPresetRow.role_preset_id == RolePresetRow.id,
        )
        .where(
            RolePresetRow.scope_type == scope_context.scope_type.to_scope_type(),
            RolePresetRow.deleted.is_(False),
        )
    )

    groups_by_id: dict[RolePresetID, _PresetRoleGroup] = {}
    for preset, permission_preset in rows:
        group = groups_by_id.setdefault(preset.id, _PresetRoleGroup(role_name=preset.name))
        if permission_preset is not None:
            group.permission_presets.append(permission_preset)
    return list(groups_by_id.values())


async def execute_scope_creator[TScopeRow: Base](
    db_sess: SASession,
    scope_creator: ScopeCreator[TScopeRow],
) -> ScopeCreatorResult[TScopeRow]:
    """Provision a scope row together with its preset-derived roles, permissions,
    and the scope's association rows.

    For every active role preset (``deleted = false``) matching the new scope's
    ``scope_type``, a role row, a role-to-scope association row, and one permission
    row per ``role_permission_presets`` entry are inserted in the same transaction
    as the scope row itself. The scope row insert is delegated to ``execute_creator``
    (``ScopeCreator`` is a ``Creator``); the surrounding rows reuse
    ``execute_bulk_creator``. Only the preset lookup is a raw read (no single-table
    querier covers the two-table join).

    The caller controls the transaction boundary (commit/rollback).
    """
    scope_spec = scope_creator.scope_spec

    scope_res = await execute_creator(db_sess, scope_creator)
    scope_context = scope_spec.extract_scope_context(scope_res.row)

    preset_groups = await _collect_preset_groups(db_sess, scope_context)
    role_rows = (
        await execute_bulk_creator(
            db_sess,
            BulkCreator(specs=[_RoleCreatorSpec(name=g.role_name) for g in preset_groups]),
        )
    ).rows

    permission_specs: list[CreatorSpec[PermissionRow]] = []
    for role, group in zip(role_rows, preset_groups, strict=True):
        for permission_preset in group.permission_presets:
            permission_specs.append(
                _PresetPermissionCreatorSpec(
                    scope_context=scope_context,
                    role_id=role.id,
                    permission_preset=permission_preset,
                )
            )
    await execute_bulk_creator(db_sess, BulkCreator(specs=permission_specs))

    association_specs: list[CreatorSpec[AssociationScopesEntitiesRow]] = [
        _RoleScopeAssociationSpec(role_id=role.id, scope_context=scope_context)
        for role in role_rows
    ]
    for parent_scope in scope_spec.parent_scopes():
        association_specs.append(
            _ParentScopeAssociationSpec(
                child_scope_context=scope_context,
                parent_scope_context=parent_scope,
            )
        )
    await execute_bulk_creator(db_sess, BulkCreator(specs=association_specs))

    return ScopeCreatorResult(scope_row=scope_res.row, role_rows=role_rows)
