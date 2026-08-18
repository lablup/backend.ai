"""Lookup specs of the v2 lineage: read one entity by an external key."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Any
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


class FieldOwnerLookup[TFieldID: FieldIdentifier, TOwnerID: EntityIdentifier](ABC):
    """Resolves a field row's id into the id of the entity that owns it.

    A field row carries no membership of its own: what it belongs to is only knowable
    through the entity owning it, which is what an action naming the row is checked and
    recorded against. The id read never reaches the service layer.

    A query rather than conditions, unlike :class:`DataLookup`, so an owner reached
    through a join is expressible. It selects the pair, so one spec serves a single row
    and a batch alike: which row each owner belongs to survives.

    Example:
        class ReplicaOwnerLookup(FieldOwnerLookup):
            def build_query(self, field_ids):
                return sa.select(ReplicaRow.id, ReplicaRow.deployment_id).where(
                    ReplicaRow.id.in_(field_ids)
                )

            def to_entity_id(self, value: UUID) -> DeploymentID:
                return DeploymentID(value)
    """

    @abstractmethod
    def build_query(
        self, field_ids: Sequence[TFieldID]
    ) -> sa.sql.Select[tuple[TFieldID, TOwnerID]]:
        """Build the query selecting each named row's id and its owning entity's id."""
        raise NotImplementedError

    @abstractmethod
    def to_entity_id(self, value: UUID) -> TOwnerID:
        """Convert the selected value into the owning entity's identifier."""
        raise NotImplementedError


class FieldOwnerKeyLookup[TOwnerID: EntityIdentifier](ABC):
    """Resolves a field row's caller-facing key into the entity that owns it.

    The counterpart of :class:`FieldOwnerLookup` for the other direction a field row is
    reached from: an access key, a name — something a request carries instead of the
    row's id. What comes back is the owner alone, because that is what the operation
    that follows is checked and recorded against.

    A query rather than conditions, for the same reason the id-keyed one is: an owner
    reached through a join is expressible.
    """

    @abstractmethod
    def build_query(self) -> sa.sql.Select[Any]:
        """Build the query selecting the owning entity's id for the key this carries."""
        raise NotImplementedError

    @abstractmethod
    def to_entity_id(self, value: UUID) -> TOwnerID:
        """Convert the selected value into the owning entity's identifier."""
        raise NotImplementedError
