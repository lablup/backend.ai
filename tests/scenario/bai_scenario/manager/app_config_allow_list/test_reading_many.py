"""여러 id로 허용 목록 항목 조회 — 원소마다 응답한다.

슈퍼관리자가 아니면 요청 전체가 막히는 것이 아니라 원소마다 거부된다. 없는 id도 마찬가지로
거부 원소이고, 빈 항목으로 반환되는 것은 검사를 통과하는 슈퍼관리자에게뿐이다.
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
    """미리 만들어 둔 둘과 존재하지 않는 id 하나를 한 번에 조회한다. 빈 목록을 줄 수도 있다."""

    nothing: bool = False

    @override
    def operation(self) -> str:
        return "batch_load_by_ids"

    @override
    def describe(self, laid: TwoEntriesAndACaller) -> str:
        if self.nothing:
            return f"{laid.caller.username}이 빈 id 목록으로 조회"
        return f"{laid.caller.username}이 항목 둘과 존재하지 않는 id를 한 번에 조회"

    @override
    async def call(self, adapter: AppConfigAllowListAdapter, laid: TwoEntriesAndACaller) -> Loaded:
        asked = (
            [] if self.nothing else [laid.first.id, laid.second.id, AppConfigAllowListID(uuid4())]
        )
        with ActingAs(laid.caller):
            return await adapter.batch_load_by_ids(asked)


@dataclass(frozen=True)
class EveryIdIsRefused(Then[TwoEntriesAndACaller, Loaded]):
    """세 항목 모두 그 항목만 거부된다."""

    @override
    def says(self) -> str:
        return "있는 둘도 없는 id도 그 항목만 거부된다"

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
            *(
                Refused(NotEnoughPermission, one if isinstance(one, BaseException) else None)
                for one in items
            ),
        ]


@dataclass(frozen=True)
class TwoNodesOneMissing(Then[TwoEntriesAndACaller, Loaded]):
    """둘은 노드, 셋째는 빈 항목."""

    @override
    def says(self) -> str:
        return "있는 둘은 노드로, 없는 id 자리는 비어서 반환된다"

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
                SameAs[object](laid.first.id, "미리 만들어 둔 첫째 항목"),
            ),
            Held[object](
                "items[1].id",
                getattr(items[1], "id", items[1]),
                SameAs[object](laid.second.id, "미리 만들어 둔 둘째 항목"),
            ),
            Same("items[2]", items[2], None),
        ]


@dataclass(frozen=True)
class NothingIsAnswered(Then[TwoEntriesAndACaller, Loaded]):
    """빈 응답."""

    @override
    def says(self) -> str:
        return "빈 응답이 반환된다"

    @override
    def look(self, laid: TwoEntriesAndACaller, answered: Answered[Loaded]) -> list[Verdict]:
        items = answered.response
        if items is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        return [Same("items", list(items), [])]


@dataclass(frozen=True)
class APlainUserIsRefusedPerId(
    Scenario[SeedingSession, TwoEntriesAndACaller, AppConfigAllowListAdapter, Loaded]
):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-is-refused-per-id"

    @override
    def describe(self) -> str:
        return (
            "슈퍼관리자가 아닌 사용자가 항목 둘과 없는 id 하나를 한 번에 조회하면, 요청 전체가 "
            "막히는 것이 아니라 세 항목 모두 그 항목만 권한 부족으로 거부된다"
        )

    @override
    def given(self) -> Given[SeedingSession, TwoEntriesAndACaller]:
        return TwoEntriesAndSomeone()

    @override
    def when(self) -> When[TwoEntriesAndACaller, AppConfigAllowListAdapter, Loaded]:
        return LoadingByIds()

    @override
    def then(self) -> Then[TwoEntriesAndACaller, Loaded]:
        return EveryIdIsRefused()


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
            "슈퍼관리자가 항목 둘과 없는 id 하나를 한 번에 조회하면, 둘은 노드로 반환되고 없는 id "
            "자리는 비어 있다. 권한 검사를 통과하는 사용자만 빈 항목을 본다"
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
        return "빈 id 목록을 주면 빈 응답이 반환된다. 하위 계층을 호출하지 않는다"

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
    TheSuperadminSeesBoth(),
    APlainUserIsRefusedPerId(),
    AnEmptyListAnswersEmpty(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_reading_many(
    scenario: LoadingStep, adapter: AppConfigAllowListAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
