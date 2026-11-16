from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

from ai.backend.testutils.scenario_steps import Answered, Same, Says, Then, Verdict
from bai_scenario.components.answers import MissingResponse


@dataclass(frozen=True)
class NothingIsFound(Then[Any, Any]):
    """훑었지만 아무것도 없다."""

    @override
    def says(self) -> str:
        return Says("응답이 비어 있습니다", english="the answer is empty")

    @override
    def look(self, laid: Any, answered: Answered[Any]) -> list[Verdict]:
        page = answered.response
        if page is None:
            return [MissingResponse(answered.raised)]
        return [
            Same("items", list(page.items), []),
            Same("total_count", page.total_count, 0),
            Same("has_next_page", page.has_next_page, False),
            Same("has_previous_page", page.has_previous_page, False),
        ]
