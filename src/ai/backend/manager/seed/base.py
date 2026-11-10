from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass
from importlib.resources.abc import Traversable
from typing import Any, override

from pydantic import ConfigDict

from ai.backend.common.exception import BackendAIError
from ai.backend.common.serde.exceptions import InvalidFileContent, UnsupportedFileFormat
from ai.backend.common.serde.loader import FileLoader
from ai.backend.common.types import BackendAISchema, SchemaValidationFailureInfo
from ai.backend.manager.errors.seed import InvalidSeedDocument
from ai.backend.manager.repositories.ops.v2.seed.types import SeedItemWrite


@dataclass(frozen=True)
class SeedRejection:
    """A seed file left unapplied, and why."""

    source: str
    reason: str


@dataclass(frozen=True)
class SeedItems[T: SeedItem]:
    """The items one seed file states."""

    source: str
    items: Sequence[T]


class SeedItem(BackendAISchema, ABC):
    """One item of a kind."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    @override
    @classmethod
    def build_validation_error(cls, info: SchemaValidationFailureInfo) -> BackendAIError:
        return InvalidSeedDocument(f"an item does not fit {cls.__name__}: {info.summary}")

    @abstractmethod
    def key(self) -> str:
        """The value identifying the item within its kind."""
        raise NotImplementedError

    @abstractmethod
    def write(self) -> SeedItemWrite:
        raise NotImplementedError

    @abstractmethod
    def check(self) -> list[str]:
        """The rules of its entity that the item's own values and sub-items break."""
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def reject(cls, files: Sequence[SeedItems[Any]]) -> list[SeedRejection]:
        """The files that fail a check spanning the items of every file of this kind."""
        raise NotImplementedError


class SeedRelationItem(SeedItem, ABC):
    """One item linking two entities by their ids. Its kind is applied after every
    entity kind."""


class RootSeed[TItem](BackendAISchema):
    """One seed file: the kind it seeds, the version it is written in, and its items.
    Every kind shares it; only the item model differs."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    @override
    @classmethod
    def build_validation_error(cls, info: SchemaValidationFailureInfo) -> BackendAIError:
        return InvalidSeedDocument(f"not a seed file: {info.summary}")

    kind: str
    version: int
    items: list[TItem]


class SeedReader:
    """Reads a seed file in the format its suffix names."""

    _loader: FileLoader

    def __init__(self) -> None:
        self._loader = FileLoader()

    def read(self, entry: Traversable) -> RootSeed[Any]:
        """The file with its items left for the kind's item model to validate."""
        try:
            content = self._loader.load(entry)
        except (UnsupportedFileFormat, InvalidFileContent) as e:
            raise InvalidSeedDocument(str(e)) from e
        return RootSeed[Any].model_validate(content)
