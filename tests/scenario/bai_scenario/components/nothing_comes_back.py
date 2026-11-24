from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

from ai.backend.testutils.scenario_steps import Says, Told, Verdict


@dataclass(frozen=True)
class NothingComesBack(Verdict):
    """응답 없이 끝나야 한다. 예외가 나거나 값이 오면 실패시킨다."""

    raised: BaseException | None
    response: Any

    @override
    def told(self) -> Told:
        if self.raised is not None:
            problems: tuple[str, ...] = (f"응답 대신 {type(self.raised).__name__} 예외가 발생했다",)
        elif self.response is not None:
            problems = ("응답이 비어 있어야 하는데 값이 왔다",)
        else:
            problems = ()
        return Told(
            Says("응답 없이 끝납니다", english="the call answers nothing"), problems=problems
        )
