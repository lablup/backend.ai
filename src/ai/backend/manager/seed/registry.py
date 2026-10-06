from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Self

from ai.backend.manager.errors.seed import InvalidSeedKindRegistry
from ai.backend.manager.seed.kind import SeedKind
from ai.backend.manager.seed.role_preset.kind import RolePresetSeedKind


class SeedKindRegistry:
    """The registered kinds, ordered so a kind comes after every kind it is applied after."""

    _kinds: dict[str, SeedKind[Any]]
    _order: list[str]

    def __init__(self, kinds: Sequence[SeedKind[Any]]) -> None:
        self._kinds = {}
        for kind in kinds:
            if kind.name() in self._kinds:
                raise InvalidSeedKindRegistry(f"{kind.name()} is registered twice")
            self._kinds[kind.name()] = kind
        for kind in kinds:
            unknown = kind.apply_after() - self._kinds.keys()
            if unknown:
                raise InvalidSeedKindRegistry(
                    f"{kind.name()} is applied after unregistered kinds {sorted(unknown)}"
                )
        self._order = self._dependency_order()

    @classmethod
    def default(cls) -> Self:
        return cls([RolePresetSeedKind()])

    def _dependency_order(self) -> list[str]:
        pending = {name: set(kind.apply_after()) for name, kind in self._kinds.items()}
        order: list[str] = []
        while pending:
            ready = sorted(name for name, needs in pending.items() if not needs)
            if not ready:
                raise InvalidSeedKindRegistry(f"{sorted(pending)} are each applied after the other")
            for name in ready:
                del pending[name]
                order.append(name)
            for needs in pending.values():
                needs.difference_update(ready)
        return order

    def get(self, name: str) -> SeedKind[Any] | None:
        return self._kinds.get(name)

    def ordered(self) -> list[SeedKind[Any]]:
        return [self._kinds[name] for name in self._order]
