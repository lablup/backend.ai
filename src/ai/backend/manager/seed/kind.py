from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel

from ai.backend.manager.models.specs.creator import EntityCreator, FieldCreator
from ai.backend.manager.models.specs.purger import FieldBatchPurger
from ai.backend.manager.models.specs.upserter import EntityUpserter, FieldUpserter


@dataclass(frozen=True)
class SeedFileItems[T: BaseModel]:
    """The items one seed file states, validated against its kind's schema."""

    source: str
    items: list[T]


@dataclass(frozen=True)
class SeedRejection:
    """A seed file left unapplied, and why."""

    source: str
    reason: str


@dataclass(frozen=True)
class SeedCreation:
    """The creators one seed item is written with: an entity and the fields it owns."""

    creator: EntityCreator[Any, Any]
    field_creators: Sequence[FieldCreator[Any, Any, Any]]


@dataclass(frozen=True)
class SeedUpsert:
    """The specs one seed item is overwritten with: what it states is rewritten, what it
    states as empty is cleared, and what it leaves out is kept."""

    upserter: EntityUpserter[Any, Any]
    field_upserters: Sequence[FieldUpserter[Any, Any, Any]]
    field_purgers: Sequence[FieldBatchPurger[Any, Any, Any]]


class SeedKind[T: BaseModel](ABC):
    """One kind of seed file: what its items look like and the specs they are written with."""

    @abstractmethod
    def name(self) -> str:
        """The `kind` a seed file states in its header."""
        raise NotImplementedError

    @abstractmethod
    def versions(self) -> frozenset[int]:
        """The spec versions this build reads."""
        raise NotImplementedError

    @abstractmethod
    def apply_after(self) -> frozenset[str]:
        """The kinds applied before this one when they come in the same run. Whether a
        referenced row exists is the database's foreign keys to answer."""
        raise NotImplementedError

    @abstractmethod
    def schema(self) -> type[T]:
        """The model one item is validated against."""
        raise NotImplementedError

    @abstractmethod
    def key(self, item: T) -> str:
        """The id the item states."""
        raise NotImplementedError

    @abstractmethod
    def reject(self, files: Sequence[SeedFileItems[T]]) -> list[SeedRejection]:
        """The files that fail a check spanning the items of every file of this kind."""
        raise NotImplementedError

    @abstractmethod
    def creation(self, item: T) -> SeedCreation:
        raise NotImplementedError

    @abstractmethod
    def upsert(self, item: T) -> SeedUpsert:
        raise NotImplementedError
