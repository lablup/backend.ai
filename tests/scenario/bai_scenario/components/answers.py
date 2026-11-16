"""어느 컴포넌트에나 나오는 답의 모양.

응답이 없다는 것과, 어느 이름으로 거부된다는 것. 컴포넌트마다 payload 타입은
다르지만 자리 이름은 같아서, 한 번 쓰고 같이 쓴다.
몇몇 컴포넌트만 쓰는 답은 `components/` 의 자기 모듈에 둔다.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

from ai.backend.testutils.scenario_steps import Answered, Refused, Says, Then, Told, Verdict


@dataclass(frozen=True)
class MissingResponse(Verdict):
    """기대한 응답이 없을 때 성공 시나리오를 실패시킨다."""

    raised: BaseException | None

    @override
    def told(self) -> Told:
        if self.raised is None:
            problem = "응답이 반환되어야 하는데 비어 있다"
        else:
            problem = f"응답 대신 {type(self.raised).__name__} 예외가 발생했다"
        return Told(Says("응답이 반환됩니다", english="a response comes back"), problems=(problem,))


@dataclass(frozen=True)
class TheCallIsRefused(Then[Any, Any]):
    """이 이름으로 거부된다."""

    expected: type[BaseException]

    @override
    def says(self) -> str:
        return Says("거부됩니다", english="the call is rejected")

    @override
    def look(self, laid: Any, answered: Answered[Any]) -> list[Verdict]:
        return [Refused(self.expected, answered.raised)]
