from __future__ import annotations

from importlib.resources import files
from importlib.resources.abc import Traversable
from typing import Final

import yaml
from pydantic import ValidationError

from ai.backend.manager.data.permission.seed.role import RoleSeed
from ai.backend.manager.errors.permission import InvalidRoleSeed

_ROLE_DIRECTORY: Final[str] = "roles"


class RoleSeedLoader:
    """Reads the role files, one seed per file, ordered by file name."""

    _directory: Traversable

    def __init__(self, directory: Traversable | None = None) -> None:
        self._directory = (
            directory if directory is not None else files(__package__).joinpath(_ROLE_DIRECTORY)
        )

    def load(self) -> list[RoleSeed]:
        seeds: list[RoleSeed] = []
        for entry in sorted(self._directory.iterdir(), key=lambda item: item.name):
            if not entry.name.endswith(".yaml"):
                continue
            seeds.append(self._read(entry))
        return seeds

    def _read(self, entry: Traversable) -> RoleSeed:
        try:
            stated = yaml.safe_load(entry.read_text(encoding="utf-8"))
        except yaml.YAMLError as e:
            raise InvalidRoleSeed(f"{entry.name} is not readable as YAML: {e}") from e
        try:
            return RoleSeed.model_validate(stated)
        except ValidationError as e:
            raise InvalidRoleSeed(f"{entry.name} does not state a role: {e}") from e
