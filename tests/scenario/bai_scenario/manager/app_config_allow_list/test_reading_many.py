"""여러 id로 허용 항목 읽기 — 원소마다 답한다.

권한이 없으면 요청 전체가 막히지 않고 그 원소만 거부된다. 없는 id도 슈퍼관리자가 아닌
사람에게는 거부 원소다. 권한 검사가 원소마다 먼저 도는데 없는 행에는 걸린 권한도 없기
때문이고, 빈 자리로 오는 것은 그 검사를 지나가는 슈퍼관리자에게뿐이다.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import override
from uuid import uuid4

import pytest
from bai_scenario.components.app_config_allow_list import (
    TwoEntriesAndACaller,
    TwoEntriesAndSomeone,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

from ai.backend.common.data.entity.app_config_allow_list import AppConfigAllowListID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.app_config_allow_list.response import (
    AppConfigAllowListNode,
)
from ai.backend.manager.api.adapters.app_config_allow_list.adapter import (
    AppConfigAllowListAdapter,
)
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    Refused,
    Same,
    SameAs,
    Scenario,
    Then,
    Verdict,
    When,
)

type Loaded = list[AppConfigAllowListNode | Exception | None]
type LoadingStep = Scenario[SeedingSession, TwoEntriesAndACaller, AppConfigAllowListAdapter, Loaded]


@dataclass(frozen=True)
class LoadingByIds(When[TwoEntriesAndACaller, AppConfigAllowListAdapter, Loaded]):
    """심은 둘과 아무것도 갖지 않은 id 하나를 한 번에 읽는다. 빈 목록을 줄 수도 있다."""

    nothing: bool = False

    @override
    def operation(self) -> str:
        return "batch_load_by_ids"

    @override
    def describe(self, laid: TwoEntriesAndACaller) -> str:
        if self.nothing:
            return f"{laid.caller.username}이 빈 id 목록으로 조회"
        return f"{laid.caller.username}이 항목 둘과 아무것도 갖지 않은 id를 한 번에 조회"

    @override
    async def call(self, adapter: AppConfigAllowListAdapter, laid: TwoEntriesAndACaller) -> Loaded:
        asked = (
            [] if self.nothing else [laid.first.id, laid.second.id, AppConfigAllowListID(uuid4())]
        )
        with ActingAs(laid.caller):
            return await adapter.batch_load_by_ids(asked)


@dataclass(frozen=True)
class OneNodeAndTwoRefused(Then[TwoEntriesAndACaller, Loaded]):
    """첫째는 노드, 둘째와 셋째는 그 자리만 거부."""

    @override
    def says(self) -> str:
        return "권한 있는 것은 노드, 볼 수 없는 것과 없는 id는 그 자리만 거부된다"

    @override
    def look(self, laid: TwoEntriesAndACaller, answered: Answered[Loaded]) -> list[Verdict]:
        items = answered.response
        if items is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        seen: list[Verdict] = [Same("items", len(items), 3)]
        if len(items) != 3:
            return seen
        second, third = items[1], items[2]
        return [
            *seen,
            Held[object](
                "items[0].id",
                getattr(items[0], "id", items[0]),
                SameAs[object](laid.first.id, "심은 첫째 항목"),
            ),
            Refused(NotEnoughPermission, second if isinstance(second, BaseException) else None),
            Refused(NotEnoughPermission, third if isinstance(third, BaseException) else None),
        ]


@dataclass(frozen=True)
class TwoNodesOneMissing(Then[TwoEntriesAndACaller, Loaded]):
    """둘은 노드, 셋째는 빈 자리."""

    @override
    def says(self) -> str:
        return "있는 둘은 노드로, 없는 id 자리는 비어서 온다"

    @override
    def look(self, laid: TwoEntriesAndACaller, answered: Answered[Loaded]) -> list[Verdict]:
        items = answered.response
        if items is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        seen: list[Verdict] = [Same("items", len(items), 3)]
        if len(items) != 3:
            return seen
        return [
            *seen,
            Held[object](
                "items[0].id",
                getattr(items[0], "id", items[0]),
                SameAs[object](laid.first.id, "심은 첫째 항목"),
            ),
            Held[object](
                "items[1].id",
                getattr(items[1], "id", items[1]),
                SameAs[object](laid.second.id, "심은 둘째 항목"),
            ),
            Same("items[2]", items[2], None),
        ]


@dataclass(frozen=True)
class NothingIsAnswered(Then[TwoEntriesAndACaller, Loaded]):
    """빈 답."""

    @override
    def says(self) -> str:
        return "빈 답이 온다"

    @override
    def look(self, laid: TwoEntriesAndACaller, answered: Answered[Loaded]) -> list[Verdict]:
        items = answered.response
        if items is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        return [Same("items", list(items), [])]


@dataclass(frozen=True)
class MixedIdsAreAnsweredEach(
    Scenario[SeedingSession, TwoEntriesAndACaller, AppConfigAllowListAdapter, Loaded]
):
    @override
    def summary(self) -> str:
        return (
            "a-readable-an-unreadable-and-a-missing-id-are-each-answered-in-order-for-a-plain-user"
        )

    @override
    def describe(self) -> str:
        return (
            "항목 둘 중 첫째에만 읽기 권한을 받은 사용자가 그 둘과 없는 id 하나를 한 번에 "
            "읽으면, 목록 순서대로 첫째는 노드, 둘째와 없는 id는 그 자리만 권한 부족으로 "
            "거부된다. 없는 행에는 걸린 권한도 없다"
        )

    @override
    def given(self) -> Given[SeedingSession, TwoEntriesAndACaller]:
        return TwoEntriesAndSomeone(reads_first=True)

    @override
    def when(self) -> When[TwoEntriesAndACaller, AppConfigAllowListAdapter, Loaded]:
        return LoadingByIds()

    @override
    def then(self) -> Then[TwoEntriesAndACaller, Loaded]:
        return OneNodeAndTwoRefused()


@dataclass(frozen=True)
class TheSuperadminSeesBoth(
    Scenario[SeedingSession, TwoEntriesAndACaller, AppConfigAllowListAdapter, Loaded]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-reads-both-and-a-missing-id-comes-back-empty"

    @override
    def describe(self) -> str:
        return (
            "슈퍼관리자가 항목 둘과 없는 id 하나를 한 번에 읽으면, 둘은 노드로 오고 없는 id "
            "자리는 비어서 온다. 권한 검사를 지나가는 사람만 빈 자리를 본다"
        )

    @override
    def given(self) -> Given[SeedingSession, TwoEntriesAndACaller]:
        return TwoEntriesAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[TwoEntriesAndACaller, AppConfigAllowListAdapter, Loaded]:
        return LoadingByIds()

    @override
    def then(self) -> Then[TwoEntriesAndACaller, Loaded]:
        return TwoNodesOneMissing()


@dataclass(frozen=True)
class AnEmptyListAnswersEmpty(
    Scenario[SeedingSession, TwoEntriesAndACaller, AppConfigAllowListAdapter, Loaded]
):
    @override
    def summary(self) -> str:
        return "an-empty-id-list-answers-empty-without-calling-anything"

    @override
    def describe(self) -> str:
        return "빈 id 목록을 주면 빈 답이 온다. 배선을 부르지 않는다"

    @override
    def given(self) -> Given[SeedingSession, TwoEntriesAndACaller]:
        return TwoEntriesAndSomeone()

    @override
    def when(self) -> When[TwoEntriesAndACaller, AppConfigAllowListAdapter, Loaded]:
        return LoadingByIds(nothing=True)

    @override
    def then(self) -> Then[TwoEntriesAndACaller, Loaded]:
        return NothingIsAnswered()


SCENARIOS: list[LoadingStep] = [
    MixedIdsAreAnsweredEach(),
    TheSuperadminSeesBoth(),
    AnEmptyListAnswersEmpty(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_reading_many(
    scenario: LoadingStep, adapter: AppConfigAllowListAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
