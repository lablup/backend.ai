from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from ai.backend.manager.seed.base import SeedItem


@dataclass(frozen=True)
class SeedKindModel:
    """A kind, the version it is read in, and the model one item is validated against."""

    name: str
    version: int
    model: type[SeedItem]


class SeedKindRegistry:
    """The registered kinds, applied in the order they are given."""

    _kinds: dict[str, SeedKindModel]

    def __init__(self, kinds: Mapping[str, tuple[int, type[SeedItem]]]) -> None:
        self._kinds = {
            name: SeedKindModel(name=name, version=version, model=model)
            for name, (version, model) in kinds.items()
        }

    def get(self, name: str) -> SeedKindModel | None:
        return self._kinds.get(name)

    def ordered(self) -> list[SeedKindModel]:
        return list(self._kinds.values())
