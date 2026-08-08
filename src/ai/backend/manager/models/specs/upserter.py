"""Upsert specs of the v2 lineage.

The two roots below are deliberately unrelated — no common ABC. See AGENTS.md
in this package before typing anything against more than one of them.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Any

from ai.backend.manager.models.base import Base
from ai.backend.manager.models.specs.membership import ScopedMembership
from ai.backend.manager.models.specs.types import IntegrityErrorCheck


class GlobalEntityUpserter[TRow: Base, TData](ABC):
    """Upsert spec of a global entity; no scope membership involved."""

    @abstractmethod
    def row_class(self) -> type[TRow]:
        raise NotImplementedError

    @abstractmethod
    def index_elements(self) -> list[str]:
        """The column names conflict detection keys on."""
        raise NotImplementedError

    @abstractmethod
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        raise NotImplementedError

    @abstractmethod
    def build_insert_values(self) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def build_update_values(self) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def to_data(self, row: TRow) -> TData:
        raise NotImplementedError


class ScopedEntityUpserter[TRow: Base, TData](ABC):
    """Upsert spec of a scope-membered entity: the row that comes back — inserted
    or updated — is registered under the create rule, idempotently."""

    @abstractmethod
    def membership(self) -> ScopedMembership[TRow]:
        """The entity's shared membership declaration."""
        raise NotImplementedError

    @abstractmethod
    def row_class(self) -> type[TRow]:
        raise NotImplementedError

    @abstractmethod
    def index_elements(self) -> list[str]:
        """The column names conflict detection keys on."""
        raise NotImplementedError

    @abstractmethod
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        raise NotImplementedError

    @abstractmethod
    def build_insert_values(self) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def build_update_values(self) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def to_data(self, row: TRow) -> TData:
        raise NotImplementedError
