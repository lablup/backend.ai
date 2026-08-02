"""Searcher for repository list queries."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import sqlalchemy as sa

from ai.backend.manager.models.base import Base
from ai.backend.manager.models.clauses import QueryCondition, QueryOrder

from .pagination import QueryPagination

if TYPE_CHECKING:
    from sqlalchemy.engine import Row


@dataclass
class Searcher[TRow: Base, TData](ABC):
    """Reads one entity as a list: what to select, how a row becomes data, and the query options.

    Self-contained counterpart of :class:`Querier`, which already carries its own
    ``row_class``: the caller hands a single object to the ops layer instead of a
    SELECT statement plus a separate options bundle.

    Subclasses live in the domain repository, so ``to_data`` names its row class
    directly and the ORM row never leaves the repository layer.

    Example:
        @dataclass
        class UserSearcher(Searcher[UserRow, UserData]):
            def build_select(self) -> sa.sql.Select[Any]:
                return sa.select(UserRow)

            def to_data(self, row: Row[Any]) -> UserData:
                user_row: UserRow = row.UserRow
                return user_row.to_data()

        async with ops.read_ops() as r:
            result = await r.search_with_scopes(scopes, UserSearcher(pagination=...))
    """

    pagination: QueryPagination
    conditions: list[QueryCondition] = field(default_factory=list)
    orders: list[QueryOrder] = field(default_factory=list)

    @abstractmethod
    def build_select(self) -> sa.sql.Select[Any]:
        """Build the base SELECT for ``TRow``, without filters, ordering, or pagination.

        Joins are allowed for filtering or ordering, but the result stays a single
        entity: an operation returning a composite row belongs in a domain-specific
        repository method instead.
        """
        raise NotImplementedError

    @abstractmethod
    def to_data(self, row: Row[Any]) -> TData:
        """Convert one fetched row into its ``data/`` type."""
        raise NotImplementedError


@dataclass
class SearcherResult[TData]:
    """Result of executing a search, carrying data types rather than ORM rows."""

    items: list[TData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool
