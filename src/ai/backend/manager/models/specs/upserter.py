"""Upsert specs of the v2 lineage.

The roots below are deliberately unrelated — no common ABC. See AGENTS.md
in this package before typing anything against more than one of them.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Collection, Sequence
from typing import Any

from ai.backend.common.data.entity.types import EntityID, EntityIdentifier
from ai.backend.manager.models.base import Base
from ai.backend.manager.models.specs.types import IntegrityErrorCheck


class GlobalEntityUpserter[TRow: Base, TData](ABC):
    """Upsert spec of a global entity: an entity that belongs under no other scope.

    The node stays provisioned idempotently, as the entity upsert does; what is absent
    is ``member_of``.
    """

    @abstractmethod
    def entity_id(self, row: TRow) -> EntityIdentifier:
        """The entity's id, read off the settled row; not necessarily the primary key.

        Answers the type too, so nothing declares it separately."""
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


class EntityUpserter[TRow: Base, TData](ABC):
    """Upsert spec of an entity: the row that comes back — inserted or updated —
    stays provisioned in the RBAC graph idempotently (node get-or-create, memberships
    registered under the create rule)."""

    @abstractmethod
    def entity_id(self, row: TRow) -> EntityIdentifier:
        """The entity's id, read off the settled row; not necessarily the primary key.

        Answers the type too, so nothing declares it separately."""
        raise NotImplementedError

    @abstractmethod
    def member_of(self, row: TRow) -> Collection[EntityIdentifier]:
        """The existing entities this one belongs to; registered idempotently."""
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
