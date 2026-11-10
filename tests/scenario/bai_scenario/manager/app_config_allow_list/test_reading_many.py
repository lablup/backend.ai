"""여러 ID로 allow_list 조회 — 입력 위치마다 응답한다.

권한이 없는 ID가 있어도 요청 전체가 실패하지 않는다. 각 입력 위치에는 노드, ``None``, 또는
해당 ID의 권한 오류가 반환된다.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import override
from uuid import uuid4

import pytest

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
    Says,
    Scenario,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.app_config_allow_list import (
    TwoEntriesAndACaller,
    TwoEntriesAndSomeone,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Loaded = list[AppConfigAllowListNode | Exception | None]
type LoadingStep = Scenario[
    TestSeedingSession, TwoEntriesAndACaller, AppConfigAllowListAdapter, Loaded
]


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
            doing_ko, doing_en = "빈 ID 목록으로 조회합니다", "loads with an empty ID list"
        elif self.duplicate_first:
            doing_ko = "첫 번째 allow_list 의 ID 를 두 번 조회합니다"
            doing_en = "loads the ID of the first allow_list twice"
        else:
            doing_ko = "allow_list 둘과 존재하지 않는 ID 를 한 번에 조회합니다"
            doing_en = "loads both allow_lists and a missing ID in one call"
        return Says(
            f"{laid.caller.username}이 {doing_ko}",
            english=f"{laid.caller.username} {doing_en}",
        )

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
        return Says(
            "있는 ID 둘과 없는 ID 모두 각 위치에 권한 오류가 반환됩니다",
            english=(
                "a permission error comes back at each position, "
                "for the two existing IDs and the missing ID alike"
            ),
        )

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
        return Says(
            "있는 ID 둘은 노드로, 없는 ID 는 None 으로 반환됩니다",
            english=("the two existing IDs come back as nodes and the missing ID as None"),
        )

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
                SameAs[object](
                    laid.first.id,
                    Says("준비한 첫 번째 ID", english="the first ID seeded in advance"),
                ),
            ),
            Held[object](
                "items[1].id",
                getattr(items[1], "id", items[1]),
                SameAs[object](
                    laid.second.id,
                    Says("준비한 두 번째 ID", english="the second ID seeded in advance"),
                ),
            ),
            Same("items[2]", items[2], None),
        ]


@dataclass(frozen=True)
class NothingIsAnswered(Then[TwoEntriesAndACaller, Loaded]):
    """빈 응답."""

    @override
    def says(self) -> str:
        return Says("빈 응답이 반환됩니다", english="an empty response comes back")

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
        return Says(
            "중복 ID 의 두 위치에 같은 allow_list 가 반환됩니다",
            english="the same allow_list comes back at both positions of the duplicate ID",
        )

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
                SameAs[object](
                    laid.first.id,
                    Says("준비한 첫 번째 ID", english="the first ID seeded in advance"),
                ),
            ),
            Held[object](
                "items[1].id",
                getattr(items[1], "id", items[1]),
                SameAs[object](
                    laid.first.id,
                    Says("준비한 첫 번째 ID", english="the first ID seeded in advance"),
                ),
            ),
        ]


@dataclass(frozen=True)
class APlainUserIsRefusedPerId(
    Scenario[TestSeedingSession, TwoEntriesAndACaller, AppConfigAllowListAdapter, Loaded]
):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-is-refused-per-id"

    @override
    def describe(self) -> str:
        return Says(
            "권한이 없는 일반 사용자가 allow_list 둘과 없는 ID 하나를 함께 조회하면, 각 입력 "
            "위치에 엔티티 읽기 권한 오류가 반환됩니다",
            english=(
                "when a plain user without permission loads both allow_lists and one missing "
                "ID together, an entity read permission error comes back at each input position"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, TwoEntriesAndACaller]:
        return TwoEntriesAndSomeone()

    @override
    def when(self) -> When[TwoEntriesAndACaller, AppConfigAllowListAdapter, Loaded]:
        return LoadingByIds()

    @override
    def then(self) -> Then[TwoEntriesAndACaller, Loaded]:
        return EveryIdIsRefused()


@dataclass(frozen=True)
class TheSuperadminSeesBoth(
    Scenario[TestSeedingSession, TwoEntriesAndACaller, AppConfigAllowListAdapter, Loaded]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-reads-both-and-a-missing-id-comes-back-empty"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 allow_list 둘과 없는 ID 하나를 함께 조회하면, "
            "입력 순서대로 노드 둘과 None 이 반환됩니다",
            english=(
                "when the superadmin loads both allow_lists and one missing ID together, "
                "two nodes and None come back in input order"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, TwoEntriesAndACaller]:
        return TwoEntriesAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[TwoEntriesAndACaller, AppConfigAllowListAdapter, Loaded]:
        return LoadingByIds()

    @override
    def then(self) -> Then[TwoEntriesAndACaller, Loaded]:
        return TwoNodesOneMissing()


@dataclass(frozen=True)
class DuplicateIdsKeepTheirPositions(
    Scenario[TestSeedingSession, TwoEntriesAndACaller, AppConfigAllowListAdapter, Loaded]
):
    @override
    def summary(self) -> str:
        return "duplicate-ids-keep-their-input-positions"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 같은 allow_list 의 ID 를 두 번 조회하면, "
            "같은 노드가 두 위치에 반환됩니다",
            english=(
                "when the superadmin loads the ID of the same allow_list twice, "
                "the same node comes back at both positions"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, TwoEntriesAndACaller]:
        return TwoEntriesAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[TwoEntriesAndACaller, AppConfigAllowListAdapter, Loaded]:
        return LoadingByIds(duplicate_first=True)

    @override
    def then(self) -> Then[TwoEntriesAndACaller, Loaded]:
        return TheDuplicateIdKeepsBothPositions()


@dataclass(frozen=True)
class AnEmptyListAnswersEmpty(
    Scenario[TestSeedingSession, TwoEntriesAndACaller, AppConfigAllowListAdapter, Loaded]
):
    @override
    def summary(self) -> str:
        return "an-empty-id-list-answers-empty"

    @override
    def describe(self) -> str:
        return Says(
            "빈 ID 목록으로 조회하면 빈 목록이 반환됩니다",
            english="loading with an empty ID list answers an empty list",
        )

    @override
    def given(self) -> Given[TestSeedingSession, TwoEntriesAndACaller]:
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
