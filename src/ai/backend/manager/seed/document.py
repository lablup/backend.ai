from __future__ import annotations

from importlib.resources.abc import Traversable
from typing import Any

from pydantic import BaseModel, ConfigDict, ValidationError

from ai.backend.common.serde.exceptions import InvalidFileContent, UnsupportedFileFormat
from ai.backend.common.serde.loader import FileLoader
from ai.backend.manager.errors.seed import InvalidSeedDocument


class SeedDocument(BaseModel):
    """One seed file: the kind it seeds, the spec version it is written in, and its items."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: str
    version: int
    items: list[Any]


class SeedDocumentReader:
    """Reads a seed file in the format its suffix names."""

    _loader: FileLoader

    def __init__(self) -> None:
        self._loader = FileLoader()

    def read(self, entry: Traversable) -> SeedDocument:
        try:
            stated = self._loader.load(entry)
        except (UnsupportedFileFormat, InvalidFileContent) as e:
            raise InvalidSeedDocument(str(e)) from e
        try:
            return SeedDocument.model_validate(stated)
        except ValidationError as e:
            raise InvalidSeedDocument(f"{entry.name} has no seed header: {e}") from e
