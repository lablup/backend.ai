from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from ai.backend.manager.errors.seed import SeedKindOutOfOrder
from ai.backend.manager.seed.base import SeedItem, SeedRelationItem
from ai.backend.manager.seed.types import SeedKind


@dataclass(frozen=True)
class SeedKindModel:
    """A kind, the version it is read in, and the model one item is validated against."""

    name: SeedKind
    version: int
    model: type[SeedItem]


class SeedKindRegistry:
    """The registered kinds, applied in the order :class:`SeedKind` declares them. A
    relation kind declared before an entity kind is refused."""

    _kinds: dict[SeedKind, SeedKindModel]

    def __init__(self, kinds: Mapping[SeedKind, tuple[int, type[SeedItem]]]) -> None:
        self._kinds = {}
        for name in SeedKind:
            if name not in kinds:
                continue
            version, model = kinds[name]
            self._kinds[name] = SeedKindModel(name=name, version=version, model=model)
        self._check_relations_last()

    def _check_relations_last(self) -> None:
        relation: SeedKindModel | None = None
        for kind in self._kinds.values():
            if issubclass(kind.model, SeedRelationItem):
                relation = relation or kind
            elif relation is not None:
                raise SeedKindOutOfOrder(
                    f"relation kind {relation.name} is declared before entity kind {kind.name}"
                )

    def get(self, name: str) -> SeedKindModel | None:
        if name not in SeedKind:
            return None
        return self._kinds.get(SeedKind(name))

    def ordered(self) -> list[SeedKindModel]:
        return list(self._kinds.values())
