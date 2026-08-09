"""Lookup spec of the v2 lineage: resolve a unique non-primary key into one entity."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence

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
