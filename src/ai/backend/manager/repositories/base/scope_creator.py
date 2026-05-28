"""Composite spec for race-free scope provisioning.

A scope-creator spec coordinates the inserts that together provision a new RBAC
scope: the scope row itself (domain, project, ...), any parent-scope mapping
rows, and roles + role-scope associations + permissions instantiated from each
active role preset matching the scope type.

The spec itself owns no table; each returned sub-spec owns exactly one table,
preserving the per-spec single-table rule. Orchestration lives in
:meth:`ScopeWriteOps.create_scope`.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass

from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.manager.models.base import Base
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.models.rbac_models.role import RoleRow

from .creator import CreatorSpec


@dataclass(frozen=True)
class ScopeContext:
    """Locator for a scope row.

    Carries the ``(scope_type, scope_id)`` pair used by downstream RBAC tables
    (``permissions``, ``association_scopes_entities``) to reference the scope.
    """

    scope_type: RBACElementType
    scope_id: str


class ScopeCreatorSpec[TScopeRow: Base](ABC):
    """Coordinator for ``scope row + parent-scope association rows``.

    Subclass per scope type (e.g. ``DomainScopeCreatorSpec``,
    ``ProjectScopeCreatorSpec``). Each returned sub-spec owns exactly one table.
    """

    @abstractmethod
    def scope_spec(self) -> CreatorSpec[TScopeRow]:
        """Single-table spec for the scope row."""
        raise NotImplementedError

    @abstractmethod
    def extract_scope_context(self, scope_row: TScopeRow) -> ScopeContext:
        """Derive ``(scope_type, scope_id)`` from the just-inserted scope row.

        The orchestrator uses this to look up matching role presets and to populate
        ``scope_id`` on derived permission and association rows.
        """
        raise NotImplementedError

    @abstractmethod
    def parent_association_specs(
        self,
        scope_row: TScopeRow,
    ) -> Sequence[CreatorSpec[AssociationScopesEntitiesRow]]:
        """Parent-scope mapping rows (e.g. project under domain).

        Return ``[]`` if the scope type has no parent.
        """
        raise NotImplementedError


@dataclass
class ScopeCreator[TScopeRow: Base]:
    """Bundles a scope-creator spec for ``ScopeWriteOps.create_scope``."""

    spec: ScopeCreatorSpec[TScopeRow]


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
