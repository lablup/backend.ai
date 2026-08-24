"""Lookup specs of the v2 lineage: read one entity by an external key."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Any
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy import Row

from ai.backend.common.data.entity.types import EntityIdentifier, FieldIdentifier
from ai.backend.manager.models.base import Base
from ai.backend.manager.models.clauses import QueryCondition


class DataLookup[TRow: Base, TEntityID: EntityIdentifier](ABC):
    """Reads one entity by a key that is not its primary key.

    A lookup resolves an external key — a name, an email within a domain, a canonical
    plus an architecture — and those are unique constraints rather than primary keys, so
    :class:`Querier` cannot express them: it carries a single ``pk_value`` and derives
    the WHERE from the table's primary key.

    Conditions rather than a SELECT, unlike :class:`~...searcher.Searcher`, so one spec
    stays one table. A key that needs a join — an image resolved through its alias table
    — is a domain repository method, not this.

    What separates it from a search is the expected cardinality, which is why
    ``lookup_entity_id`` reads at most two rows and rejects the second: matching more than one
    means the key is not unique, and answering with an arbitrary one would hide that.

    Answers the id alone. The value behind it is read by a get, which carries its own
    querier and can say what to load; a lookup that also produced the value would decide
    that for every caller.

    Example:
        class UserByEmail(DataLookup[UserRow, UserID]):
            def row_class(self) -> type[UserRow]:
                return UserRow

            def conditions(self) -> Sequence[QueryCondition]:
                return [
                    lambda: UserRow.email == self._email,
                    lambda: UserRow.domain_name == self._domain,
                ]

            def to_entity_id(self, row: UserRow) -> UserID:
                return UserID(row.uuid)

        async with ops.read_ops() as r:
            user_id = await r.lookup_entity_id(UserByEmail(email, domain))
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
    def to_entity_id(self, row: TRow) -> TEntityID:
        """Return the id of the entity the matched row is."""
        raise NotImplementedError


class FieldOwnerLookup[TFieldID: FieldIdentifier, TOwnerID: EntityIdentifier](ABC):
    """Resolves a field row's id into the id of the entity that owns it.

    A field row carries no membership of its own: what it belongs to is only knowable
    through the entity owning it, which is what an action naming the row is checked and
    recorded against. The id read never reaches the service layer.

    A query rather than conditions, unlike :class:`DataLookup`, so an owner reached
    through a join is expressible. It selects the pair, so one spec serves a single row
    and a batch alike: which row each owner belongs to survives.

    ``to_entity_id`` takes the selected row rather than one value off it, as
    :class:`DataLookup` does: an identifier answers for the entity it names, and where
    the reference is polymorphic the type is a second value only the row carries.

    Example:
        class ReplicaOwnerLookup(FieldOwnerLookup):
            def build_query(self, field_ids):
                return sa.select(ReplicaRow.id, ReplicaRow.deployment_id).where(
                    ReplicaRow.id.in_(field_ids)
                )

            def to_entity_id(self, row: Row[Any]) -> DeploymentID:
                return DeploymentID(row[1])
    """

    @abstractmethod
    def build_query(self, field_ids: Sequence[TFieldID]) -> sa.sql.Select[Any]:
        """Build the query selecting each named row's id first and whatever
        ``to_entity_id`` builds the owner's identifier from after it."""
        raise NotImplementedError

    @abstractmethod
    def to_entity_id(self, row: Row[Any]) -> TOwnerID:
        """Convert one selected row into the owning entity's identifier."""
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


class FieldKeyLookup[TFieldID: FieldIdentifier, TOwnerID: EntityIdentifier](ABC):
    """Resolves a field row's caller-facing key into that row's id and its owner's.

    An operation naming a field row takes the row's id, but a request carries an access
    key or a name instead. This is the step between: one query answers both, because the
    id is what the operation names the row by and the owner is what this run itself is
    recorded against.

    A query rather than conditions, for the same reason :class:`FieldOwnerKeyLookup` is
    one: an owner reached through a join is expressible.
    """

    @abstractmethod
    def build_query(self) -> sa.sql.Select[Any]:
        """Build the query selecting the field row's id and its owner's, in that order."""
        raise NotImplementedError

    @abstractmethod
    def to_field_id(self, value: UUID) -> TFieldID:
        """Convert the first selected value into the field row's identifier."""
        raise NotImplementedError

    @abstractmethod
    def to_entity_id(self, value: UUID) -> TOwnerID:
        """Convert the second selected value into the owning entity's identifier."""
        raise NotImplementedError
