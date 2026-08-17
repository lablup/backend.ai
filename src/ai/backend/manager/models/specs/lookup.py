"""Lookup specs of the v2 lineage: read one entity by an external key."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from uuid import UUID

import sqlalchemy as sa

from ai.backend.common.data.entity.types import EntityIdentifier, FieldIdentifier
from ai.backend.manager.models.base import Base
from ai.backend.manager.models.clauses import QueryCondition


class DataLookup[TRow: Base, TData](ABC):
    """Reads one entity by a key that is not its primary key.

    A lookup resolves an external key — a name, an email within a domain, a canonical
    plus an architecture — and those are unique constraints rather than primary keys, so
    :class:`Querier` cannot express them: it carries a single ``pk_value`` and derives
    the WHERE from the table's primary key.

    Conditions rather than a SELECT, unlike :class:`~...searcher.Searcher`, so one spec
    stays one table. A key that needs a join — an image resolved through its alias table
    — is a domain repository method, not this.

    What separates it from a search is the expected cardinality, which is why
    ``lookup_data`` reads at most two rows and rejects the second: matching more than one
    means the key is not unique, and answering with an arbitrary one would hide that.

    Example:
        class UserByEmail(DataLookup[UserRow, UserData]):
            def row_class(self) -> type[UserRow]:
                return UserRow

            def conditions(self) -> Sequence[QueryCondition]:
                return [
                    lambda: UserRow.email == self._email,
                    lambda: UserRow.domain_name == self._domain,
                ]

            def to_data(self, row: UserRow) -> UserData:
                return row.to_data()

        async with ops.read_ops() as r:
            user = await r.lookup_data(UserByEmail(email, domain))
    """

    @abstractmethod
    def row_class(self) -> type[TRow]:
        """Return the ORM class the key resolves within."""
        raise NotImplementedError

    @abstractmethod
    def conditions(self) -> Sequence[QueryCondition]:
        """Return the key's conditions, AND combined."""
        raise NotImplementedError

    @abstractmethod
    def to_data(self, row: TRow) -> TData:
        """Convert the matched row into its ``data/`` type."""
        raise NotImplementedError


class FieldOwnerLookup(ABC):
    """Resolves a field row's id into the id of the entity that owns it.

    A field row is absent from the RBAC graph, so an action naming one has nothing to
    authorize against until this runs. The id it reads never reaches the service layer:
    it names the target of the permission check and of the audit row.

    A query rather than conditions, unlike :class:`DataLookup`, so an owner reached
    through a join is expressible and only the id is read. The row is named by an
    argument, so the owner read is that of the id the action declares.

    Example:
        class ObjectStorageOwnerLookup(FieldOwnerLookup):
            def build_query(self, field_id: FieldIdentifier) -> sa.sql.Select[tuple[UUID]]:
                return sa.select(ObjectStorageRow.storage_namespace_id).where(
                    ObjectStorageRow.id == field_id
                )

            def to_entity_id(self, value: UUID) -> StorageNamespaceID:
                return StorageNamespaceID(value)
    """

    @abstractmethod
    def build_query(self, field_id: FieldIdentifier) -> sa.sql.Select[tuple[UUID]]:
        """Build the query selecting the owning entity's id, matching at most one row."""
        raise NotImplementedError

    @abstractmethod
    def to_entity_id(self, value: UUID) -> EntityIdentifier:
        """Convert the selected value into the owning entity's identifier."""
        raise NotImplementedError
