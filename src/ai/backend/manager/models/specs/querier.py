"""Single-row read specs of the v2 lineage, keyed by the entity id, the owner, or the
field row's own id."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import sqlalchemy as sa
from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.types import EntityIdentifier, FieldData, FieldIdentifier
from ai.backend.manager.models.base import Base


class DataQuerier[TRow: Base, TData](ABC):
    """Reads one entity: which row to fetch, and how that row becomes data.

    Self-contained counterpart of :class:`Querier`, in the same sense
    :class:`~ai.backend.manager.repositories.base.searcher.Searcher` is one for batch
    queries. Carrying ``to_data`` is the point: the ops layer returns the ``data/`` type
    and the ORM row never leaves it, so no caller has to know that rows have a
    ``to_data`` at all.

    Subclasses live in the domain repository, which is what lets ``to_data`` name its
    row class directly.

    Example:
        class UserQuerier(DataQuerier[UserRow, UserData]):
            def row_class(self) -> type[UserRow]:
                return UserRow

            def entity_id_column(self) -> InstrumentedAttribute[Any]:
                return UserRow.uuid

            def entity_id_value(self) -> UserID:
                return self._user_id

            def to_data(self, row: UserRow) -> UserData:
                return row.to_data()

        async with ops.read_ops() as r:
            user = await r.query_data(UserQuerier(user_id))
    """

    @abstractmethod
    def row_class(self) -> type[TRow]:
        """Return the ORM class the row is read from."""
        raise NotImplementedError

    @abstractmethod
    def entity_id_column(self) -> InstrumentedAttribute[Any]:
        """Return the column that carries the entity id.

        Named rather than derived from the primary key, because the two part ways: a
        table whose key is a name (``domains.name``, ``resource_slot_types.slot_name``)
        still identifies its entity by a uuid column beside it.
        """
        raise NotImplementedError

    @abstractmethod
    def entity_id_value(self) -> EntityIdentifier:
        """Return the id of the entity to read."""
        raise NotImplementedError

    @abstractmethod
    def to_data(self, row: TRow) -> TData:
        """Convert the fetched row into its ``data/`` type."""
        raise NotImplementedError


class OwnedFieldQuerier[TOwnerID: EntityIdentifier, TRow: Base, TData: FieldData](ABC):
    """The one field row each named entity designates.

    A querier rather than a :class:`~...searcher.Searcher`: an owner designates exactly
    one row, so the answer is one per owner and a second row for the same owner is a
    fault, not a page that happens to be longer. Keyed by the owner, which is what a
    field operation is authorized and recorded against.

    What makes a row the designated one belongs in ``build_select``; the ops layer adds
    the owner filter and keys the answer by ``owner_id_column``.
    """

    @abstractmethod
    def build_select(self) -> sa.sql.Select[Any]:
        """Build the SELECT narrowed to designated rows, without the owner filter."""
        raise NotImplementedError

    @abstractmethod
    def owner_id_column(self) -> InstrumentedAttribute[Any]:
        """Return the column naming the entity a row belongs to."""
        raise NotImplementedError

    @abstractmethod
    def to_data(self, row: TRow) -> TData:
        """Convert the designated row into its ``data/`` type."""
        raise NotImplementedError


class FieldQuerier[TRow: Base, TData: FieldData](ABC):
    """Reads one field row by its own id.

    Separate from :class:`DataQuerier` because a field row's id is no
    ``EntityIdentifier``: it names a row, not an entity, and what the read is authorized
    against is the owner the lookup reads. Keyed the way :class:`~...purger.FieldPurger`
    keys its delete.
    """

    @abstractmethod
    def row_class(self) -> type[TRow]:
        """Return the ORM class the row is read from."""
        raise NotImplementedError

    @abstractmethod
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        """Return the column carrying the field id, which the read keys on."""
        raise NotImplementedError

    @abstractmethod
    def target_id_value(self) -> FieldIdentifier:
        """Return the id of the field row to read."""
        raise NotImplementedError

    @abstractmethod
    def to_data(self, row: TRow) -> TData:
        """Convert the fetched row into its ``data/`` type."""
        raise NotImplementedError
