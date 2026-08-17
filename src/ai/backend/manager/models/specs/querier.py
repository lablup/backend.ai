"""Single-row read specs of the v2 lineage: fetch by primary key."""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

import sqlalchemy as sa

from ai.backend.common.data.entity.types import EntityIdentifier
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

            def pk_value(self) -> UUID:
                return self._user_id

            def to_data(self, row: UserRow) -> UserData:
                return row.to_data()

        async with ops.read_ops() as r:
            user = await r.query_data(UserQuerier(user_id))
    """

    @abstractmethod
    def row_class(self) -> type[TRow]:
        """Return the ORM class for table access and PK detection."""
        raise NotImplementedError

    @abstractmethod
    def pk_value(self) -> UUID | str | int:
        """Return the primary key value identifying the target row."""
        raise NotImplementedError

    @abstractmethod
    def to_data(self, row: TRow) -> TData:
        """Convert the fetched row into its ``data/`` type."""
        raise NotImplementedError


class FieldOwnerQuerier(ABC):
    """Reads the id of the entity that owns one field row.

    A field row is absent from the RBAC graph, so an action naming one has no entity to
    authorize against until this resolves it. The value never reaches the service layer:
    it names the target of the permission check and the audit row.

    A query rather than a column, so an owner reached through a join is expressible.

    Example:
        class ObjectStorageOwnerQuerier(FieldOwnerQuerier):
            def build_query(self) -> sa.sql.Select[tuple[UUID]]:
                return sa.select(ObjectStorageRow.storage_namespace_id).where(
                    ObjectStorageRow.id == self._object_storage_id
                )

            def to_entity_id(self, value: UUID) -> StorageNamespaceID:
                return StorageNamespaceID(value)
    """

    @abstractmethod
    def build_query(self) -> sa.sql.Select[tuple[UUID]]:
        """Build the query selecting the owning entity's id, which must match at most
        one row."""
        raise NotImplementedError

    @abstractmethod
    def to_entity_id(self, value: UUID) -> EntityIdentifier:
        """Convert the selected value into the owning entity's identifier."""
        raise NotImplementedError
