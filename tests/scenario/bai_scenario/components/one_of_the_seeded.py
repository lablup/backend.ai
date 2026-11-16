from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

from ai.backend.testutils.scenario_steps import Condition, Says


@dataclass(frozen=True)
class OneOfTheSeeded(Condition[list[tuple[Any, ...]]]):
    """답의 항목이 미리 저장한 행들 가운데 하나다.

    순서를 정하는 조건이 없는 검색은 어느 행이 한 쪽에 오는지 정해져 있지 않다. 항목 수와
    항목의 모든 값은 확인하되, 어느 행인지는 이 조건이 가린다.
    """

    options: frozenset[tuple[Any, ...]]
    named: Says | str

    @override
    def says(self) -> str:
        return self.named if isinstance(self.named, Says) else Says(self.named)

    @override
    def holds(self, got: list[tuple[Any, ...]]) -> bool:
        return len(got) == 1 and got[0] in self.options
