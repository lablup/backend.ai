"""어느 컴포넌트에나 나오는 답의 모양.

한 페이지가 비어 있다는 것과, 어느 이름으로 거부된다는 것. 컴포넌트마다 payload 타입은
다르지만 자리 이름은 같아서, 한 번 쓰고 같이 쓴다.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

from ai.backend.testutils.scenario_steps import (
    Answered,
    Condition,
    Refused,
    Same,
    Says,
    Then,
    Told,
    Verdict,
)


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
class RefusedItem(Verdict):
    """여럿을 받는 호출이 이 항목 하나를 이 이름의 거부로 실패 목록에 돌려준다.

    레포트는 거부 말머리로 이 행을 거부 행으로 센다. 실패 이유는 `reason`을 담는다.
    """

    called: str
    expected: type[BaseException]
    reason: str
    message: str | None

    @override
    def told(self) -> Told:
        says = Says(
            f"{Refused.PREFIX}{self.called}: {self.expected.__name__}",
            english=f"rejected: {self.called}: {self.expected.__name__}",
        )
        if self.message is None:
            return Told(says, problems=(f"{says} 이어야 하는데 실패 목록에 없다",))
        if self.reason not in self.message:
            return Told(says, problems=(f"{says} 이어야 하는데 이유가 '{self.message}'",))
        return Told(says)


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


@dataclass(frozen=True)
class TheFailedItemIsRefused(Verdict):
    """A partial bulk answer's failed item, marked as the refusal this row expected.

    The call answers with a failed list instead of raising, so the item's reason is
    checked and the line carries the refusal mark the report counts.
    """

    at: str
    message: str
    reason: str

    @override
    def told(self) -> Told:
        says = Says(
            f"{Refused.PREFIX}{self.at}: {self.reason}",
            f"rejected: {self.at}: {self.reason}",
        )
        if self.reason not in self.message:
            return Told(
                says,
                problems=(f"{self.at}: {self.reason!r} 이어야 하는데 {self.message!r}",),
            )
        return Told(says)
