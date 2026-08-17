"""Single-row read spec of the v2 lineage: fetch by primary key."""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

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
