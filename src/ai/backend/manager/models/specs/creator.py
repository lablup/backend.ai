"""Insert specs of the v2 lineage.

The three roots below are deliberately unrelated — no common ABC. See AGENTS.md
in this package before typing anything against more than one of them.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence

from ai.backend.common.identifier.entity import EntityID
from ai.backend.manager.models.base import Base
from ai.backend.manager.models.specs.membership import ScopedMembership
from ai.backend.manager.models.specs.types import IntegrityErrorCheck


class GlobalEntityCreator[TRow: Base, TData](ABC):
    """Insert spec of a global entity — system-wide state outside the scope
    hierarchy; creating a row registers no scope membership."""

    @abstractmethod
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        raise NotImplementedError

    @abstractmethod
    def build_row(self) -> TRow:
        raise NotImplementedError

    @abstractmethod
    def to_data(self, row: TRow) -> TData:
        raise NotImplementedError


class FieldEntityCreator[TOwnerID: EntityID, TRow: Base, TData](ABC):
    """Insert spec of a field row — a row owned by another entity.

    Built only from the owner's settled identifier (e.g. a just-created parent's
    id), so a field row cannot be created standalone. No scope membership is
    registered: writing a field row is authorized through the owner, like an
    update to the owning entity.
    """

    @abstractmethod
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        raise NotImplementedError

    @abstractmethod
    def build_row(self, owner_id: TOwnerID) -> TRow:
        raise NotImplementedError

    @abstractmethod
    def to_data(self, row: TRow) -> TData:
        raise NotImplementedError


class ScopedEntityCreator[TRow: Base, TData](ABC):
    """Insert spec of a scope-membered entity: creating a row always registers it
    under its declared parent scope.

    A separate root from :class:`GlobalEntityCreator`, the way the scoped and global
    search paths are separate: which lifecycle applies is visible in the spec type,
    and a scoped spec cannot slip through the registration-free path.
    """

    @abstractmethod
    def membership(self) -> ScopedMembership[TRow]:
        """The entity's shared membership declaration."""
        raise NotImplementedError

    @abstractmethod
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        raise NotImplementedError

    @abstractmethod
    def build_row(self) -> TRow:
        raise NotImplementedError

    @abstractmethod
    def to_data(self, row: TRow) -> TData:
        raise NotImplementedError
