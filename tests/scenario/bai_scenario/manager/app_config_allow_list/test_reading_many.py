"""여러 ID로 허용 목록 항목 조회 — 입력 위치마다 응답한다.

권한이 없는 ID가 있어도 요청 전체가 실패하지 않는다. 각 입력 위치에는 노드, ``None``, 또는
해당 ID의 권한 오류가 반환된다.
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
    """준비한 ID 둘과 존재하지 않는 ID를 조회한다. 빈 목록도 허용한다."""

    nothing: bool = False
    duplicate_first: bool = False

    @override
    def operation(self) -> str:
        return "batch_load_by_ids"

    @override
    def describe(self, laid: TwoEntriesAndACaller) -> str:
        if self.nothing:
            return f"{laid.caller.username}이 빈 ID 목록으로 조회"
        if self.duplicate_first:
            return f"{laid.caller.username}이 첫 번째 허용 목록 항목의 ID를 두 번 조회"
        return f"{laid.caller.username}이 항목 둘과 존재하지 않는 ID를 한 번에 조회"

    @override
    async def call(self, adapter: AppConfigAllowListAdapter, laid: TwoEntriesAndACaller) -> Loaded:
        if self.nothing:
            asked = []
        elif self.duplicate_first:
            asked = [laid.first.id, laid.first.id]
        else:
            asked = [laid.first.id, laid.second.id, AppConfigAllowListID(uuid4())]
        with ActingAs(laid.caller):
            return await adapter.batch_load_by_ids(asked)


@dataclass(frozen=True)
class EveryIdIsRefused(Then[TwoEntriesAndACaller, Loaded]):
    """세 입력 위치에 각각 권한 오류가 반환된다."""

    @override
    def says(self) -> str:
        return "있는 ID 둘과 없는 ID 모두 각 위치에 권한 오류가 반환된다"

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
    """존재하는 ID는 노드, 존재하지 않는 ID는 ``None``으로 반환된다."""

    @override
    def says(self) -> str:
        return "있는 ID 둘은 노드로, 없는 ID는 None으로 반환된다"

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
class TheDuplicateIdKeepsBothPositions(Then[TwoEntriesAndACaller, Loaded]):
    """같은 ID를 두 번 요청하면 두 위치에 같은 노드가 반환된다."""

    @override
    def says(self) -> str:
        return "중복 ID의 두 위치에 같은 허용 목록 항목이 반환된다"

    @override
    def look(self, laid: TwoEntriesAndACaller, answered: Answered[Loaded]) -> list[Verdict]:
        items = answered.response
        if items is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        seen: list[Verdict] = [Same("items", len(items), 2)]
        if len(items) != 2:
            return seen
        return [
            *seen,
            Held[object](
                "items[0].id",
                getattr(items[0], "id", items[0]),
                SameAs[object](laid.first.id, "준비한 첫 번째 허용 목록 항목"),
            ),
            Held[object](
                "items[1].id",
                getattr(items[1], "id", items[1]),
                SameAs[object](laid.first.id, "준비한 첫 번째 허용 목록 항목"),
            ),
        ]


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
            "권한이 없는 일반 사용자가 항목 둘과 없는 ID 하나를 함께 조회하면, 각 입력 위치에 "
            "엔티티 읽기 권한 오류가 반환된다"
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
            "슈퍼관리자가 항목 둘과 없는 ID 하나를 함께 조회하면, 입력 순서대로 노드 둘과 "
            "None이 반환된다"
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
class DuplicateIdsKeepTheirPositions(
    Scenario[SeedingSession, TwoEntriesAndACaller, AppConfigAllowListAdapter, Loaded]
):
    @override
    def summary(self) -> str:
        return "duplicate-ids-keep-their-input-positions"

    @override
    def describe(self) -> str:
        return (
            "슈퍼관리자가 같은 허용 목록 항목의 ID를 두 번 조회하면, 같은 노드가 두 위치에 반환된다"
        )

    @override
    def given(self) -> Given[SeedingSession, TwoEntriesAndACaller]:
        return TwoEntriesAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[TwoEntriesAndACaller, AppConfigAllowListAdapter, Loaded]:
        return LoadingByIds(duplicate_first=True)

    @override
    def then(self) -> Then[TwoEntriesAndACaller, Loaded]:
        return TheDuplicateIdKeepsBothPositions()


@dataclass(frozen=True)
class AnEmptyListAnswersEmpty(
    Scenario[SeedingSession, TwoEntriesAndACaller, AppConfigAllowListAdapter, Loaded]
):
    @override
    def summary(self) -> str:
        return "an-empty-id-list-answers-empty"

    @override
    def describe(self) -> str:
        return "빈 ID 목록으로 조회하면 빈 목록이 반환된다"

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
    DuplicateIdsKeepTheirPositions(),
    APlainUserIsRefusedPerId(),
    AnEmptyListAnswersEmpty(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_reading_many(
    scenario: LoadingStep, adapter: AppConfigAllowListAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
