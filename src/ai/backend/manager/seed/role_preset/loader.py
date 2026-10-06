from __future__ import annotations

from importlib.resources.abc import Traversable
from typing import ClassVar

from pydantic import ValidationError

from ai.backend.manager.errors.permission import InvalidRoleSeed
from ai.backend.manager.errors.seed import InvalidSeedDocument
from ai.backend.manager.seed.document import SeedDocumentReader
from ai.backend.manager.seed.role_preset.role import RoleSeed


class RoleSeedLoader:
    """Reads the role files of a directory, ordered by file name. Each file is a
    `role_preset` seed file."""

    kind: ClassVar[str] = "role_preset"
    versions: ClassVar[frozenset[int]] = frozenset({1})

    _directory: Traversable
    _reader: SeedDocumentReader

    def __init__(self, directory: Traversable) -> None:
        self._directory = directory
        self._reader = SeedDocumentReader()

    def load(self) -> list[RoleSeed]:
        seeds: list[RoleSeed] = []
        for entry in sorted(self._directory.iterdir(), key=lambda item: item.name):
            if not entry.name.endswith(".yaml"):
                continue
            seeds.extend(self._read(entry))
        return seeds

    def _read(self, entry: Traversable) -> list[RoleSeed]:
        try:
            document = self._reader.read(entry)
        except InvalidSeedDocument as e:
            raise InvalidRoleSeed(str(e)) from e
        if document.kind != self.kind:
            raise InvalidRoleSeed(f"{entry.name} seeds {document.kind!r}, not {self.kind!r}")
        if document.version not in self.versions:
            raise InvalidRoleSeed(f"{entry.name} is written in version {document.version}")
        try:
            return [RoleSeed.model_validate(item) for item in document.items]
        except ValidationError as e:
            raise InvalidRoleSeed(f"{entry.name} does not state a role: {e}") from e
