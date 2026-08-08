"""Delete specs of the v2 lineage.

The three roots below are deliberately unrelated — no common ABC. See AGENTS.md
in this package before typing anything against more than one of them.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from uuid import UUID

from ai.backend.manager.models.base import Base
from ai.backend.manager.models.specs.membership import ScopedMembership
from ai.backend.manager.models.specs.types import ConflictCheck


class GlobalEntityPurger[TRow: Base, TData](ABC):
    """Delete spec of a global entity; no scope membership to remove."""

    @abstractmethod
    def row_class(self) -> type[TRow]:
        raise NotImplementedError

    @abstractmethod
    def pk_value(self) -> UUID | str | int:
        raise NotImplementedError

    @abstractmethod
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        raise NotImplementedError

    @abstractmethod
    def to_data(self, row: TRow) -> TData:
        raise NotImplementedError


class FieldEntityPurger[TRow: Base, TData](ABC):
    """Delete spec of a field row — authorized through its owner, like an update
    to the owning entity; no scope membership to remove."""

    @abstractmethod
    def row_class(self) -> type[TRow]:
        raise NotImplementedError

    @abstractmethod
    def pk_value(self) -> UUID | str | int:
        raise NotImplementedError

    @abstractmethod
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        raise NotImplementedError

    @abstractmethod
    def to_data(self, row: TRow) -> TData:
        raise NotImplementedError


class ScopedEntityPurger[TRow: Base, TData](ABC):
    """Delete spec of a scope-membered entity: purging a row removes its declared
    membership with it, symmetrically with the scoped create."""

    @abstractmethod
    def membership(self) -> ScopedMembership[TRow]:
        """The entity's shared membership declaration."""
        raise NotImplementedError

    @abstractmethod
    def row_class(self) -> type[TRow]:
        raise NotImplementedError

    @abstractmethod
    def pk_value(self) -> UUID | str | int:
        raise NotImplementedError

    @abstractmethod
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        raise NotImplementedError

    @abstractmethod
    def to_data(self, row: TRow) -> TData:
        raise NotImplementedError
