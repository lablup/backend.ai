"""Composite spec for race-free scope teardown.

Mirror of :mod:`scope_creator`. A scope-purger spec only locates the scope to
tear down; the orchestrator runs the inverse sequence: drop scope-bound
permission rows, drop the scope's association rows, and finally drop the scope
row itself.

Roles are intentionally left alone — role lifecycle is independent of scope
lifecycle, and a role may be reused or reassigned after a scope is gone.

The permission and association rows are deleted generically from the scope's
:class:`ScopeContext`: they are written uniformly at provisioning time
(``scope_type`` / ``scope_id`` on permissions; the scope referenced as scope or
as entity on associations), so the inverse filter needs no per-scope-type spec.
Orchestration lives in :meth:`ScopeWriteOps.purge_scope`.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from uuid import UUID

from ai.backend.manager.models.base import Base

from .scope_creator import ScopeContext


class ScopePurgerSpec[TScopeRow: Base](ABC):
    """Locator for a scope to purge along with the scope-bound RBAC rows it leaves behind.

    Subclass per scope type. The orchestrator derives the permission and
    association deletions from :meth:`scope_context`; the spec only needs to
    identify the scope row itself.
    """

    @abstractmethod
    def scope_row_class(self) -> type[TScopeRow]:
        """ORM class of the scope row being purged."""
        raise NotImplementedError

    @abstractmethod
    def scope_pk_value(self) -> UUID | str:
        """Primary-key value of the scope row to delete."""
        raise NotImplementedError

    @abstractmethod
    def scope_context(self) -> ScopeContext:
        """``(scope_type, scope_id)`` locator for the scope-bound RBAC rows.

        The orchestrator uses this to delete every permission row pinned to the
        scope and every association row that references the scope (as scope or as
        entity), mirroring how those rows were written at provisioning time.
        """
        raise NotImplementedError


@dataclass
class ScopePurger[TScopeRow: Base]:
    """Bundles a scope-purger spec for ``ScopeWriteOps.purge_scope``."""

    spec: ScopePurgerSpec[TScopeRow]


@dataclass
class ScopePurgerResult[TScopeRow: Base]:
    """Outcome of a scope teardown."""

    scope_row: TScopeRow | None
    deleted_permission_count: int
    deleted_association_count: int
