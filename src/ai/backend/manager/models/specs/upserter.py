"""Upsert specs of the v2 lineage.

The roots below are deliberately unrelated — no common ABC. See AGENTS.md
in this package before typing anything against more than one of them.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Collection, Sequence
from typing import Any, final

from ai.backend.common.data.entity.types import ScopeRef, ScopeType
from ai.backend.common.identifier.entity import EntityID
from ai.backend.common.identifier.scope import ScopeID
from ai.backend.manager.models.base import Base
from ai.backend.manager.models.specs.types import IntegrityErrorCheck


class GlobalEntityUpserter[TRow: Base, TData](ABC):
    """Upsert spec of a global entity; no scope involved."""

    @abstractmethod
    def row_class(self) -> type[TRow]:
        raise NotImplementedError

    @abstractmethod
    def index_elements(self) -> list[str]:
        """The column names conflict detection keys on."""
        raise NotImplementedError

    @abstractmethod
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        raise NotImplementedError

    @abstractmethod
    def build_insert_values(self) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def build_update_values(self) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def to_data(self, row: TRow) -> TData:
        raise NotImplementedError


class EntityUpserter[TRow: Base, TData](ABC):
    """Upsert spec of an entity: the row that comes back — inserted or updated —
    keeps its scope provisioned idempotently (virtual scope node get-or-create,
    memberships registered under the create rule)."""

    @abstractmethod
    def scope_type(self) -> ScopeType:
        raise NotImplementedError

    @abstractmethod
    def scope_id(self, row: TRow) -> ScopeID:
        raise NotImplementedError

    @final
    def scope_of(self, row: TRow) -> ScopeRef:
        return ScopeRef(scope_type=self.scope_type(), scope_id=self.scope_id(row))

    @abstractmethod
    def member_of(self, row: TRow) -> Collection[ScopeRef]:
        """The existing scopes the entity belongs to; registered idempotently."""
        raise NotImplementedError

    @abstractmethod
    def row_class(self) -> type[TRow]:
        raise NotImplementedError

    @abstractmethod
    def index_elements(self) -> list[str]:
        """The column names conflict detection keys on."""
        raise NotImplementedError

    @abstractmethod
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        raise NotImplementedError

    @abstractmethod
    def build_insert_values(self) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def build_update_values(self) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def to_data(self, row: TRow) -> TData:
        raise NotImplementedError


class FieldUpserter[TOwnerID: EntityID, TRow: Base, TData](ABC):
    """Upsert spec of a field row — built only under the owner's settled
    identifier, like the field create; no scope involved."""

    @abstractmethod
    def row_class(self) -> type[TRow]:
        raise NotImplementedError

    @abstractmethod
    def index_elements(self) -> list[str]:
        """The column names conflict detection keys on."""
        raise NotImplementedError

    @abstractmethod
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        raise NotImplementedError

    @abstractmethod
    def build_insert_values(self, owner_id: TOwnerID) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def build_update_values(self) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def to_data(self, row: TRow) -> TData:
        raise NotImplementedError
