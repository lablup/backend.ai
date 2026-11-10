"""여러 id로 설정 조각 조회 — 원소마다 응답한다.

권한이 없으면 요청 전체가 막히지 않고 그 원소만 거부된다. 없는 id도 슈퍼관리자가 아닌
사용자에게는 거부 원소다. 권한 검사가 원소마다 먼저 실행되는데 없는 행에는 부여된 권한도
없기 때문이고, 빈 항목으로 반환되는 것은 그 검사를 통과하는 슈퍼관리자에게뿐이다.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import override
from uuid import uuid4

import pytest

from ai.backend.common.data.entity.app_config_fragment import AppConfigFragmentID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.app_config_fragment.response import AppConfigFragmentNode
from ai.backend.manager.api.adapters.app_config_fragment.adapter import AppConfigFragmentAdapter
from ai.backend.manager.data.permission.types import Permission
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
from bai_scenario.components.app_config_fragment import (
    SomeFragmentsAndACaller,
    SomeFragmentsAndSomeone,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Loaded = list[AppConfigFragmentNode | Exception | None]
type LoadingStep = Scenario[
    TestSeedingSession, SomeFragmentsAndACaller, AppConfigFragmentAdapter, Loaded
]


@dataclass(frozen=True)
class LoadingByIds(When[SomeFragmentsAndACaller, AppConfigFragmentAdapter, Loaded]):
    """자기 조각, 남의 조각, 존재하지 않는 id를 한 번에 조회한다. 빈 목록을 줄 수도 있다."""

    nothing: bool = False

    @override
    def operation(self) -> str:
        return "batch_load_by_ids"

    @override
    def describe(self, laid: SomeFragmentsAndACaller) -> str:
        if self.nothing:
            return Says(
                f"{laid.caller.username} 이 빈 id 목록으로 조회합니다",
                english=f"{laid.caller.username} reads with an empty id list",
            )
        return Says(
            f"{laid.caller.username} 이 자기 조각, 다른 사용자의 조각, 존재하지 않는 id 를 "
            "한 번에 조회합니다",
            english=(
                f"{laid.caller.username} reads their own fragment, another user's fragment "
                "and a missing id at once"
            ),
        )

    @override
    async def call(
        self, adapter: AppConfigFragmentAdapter, laid: SomeFragmentsAndACaller
    ) -> Loaded:
        asked = (
            [] if self.nothing else [laid.mine[0].id, laid.theirs.id, AppConfigFragmentID(uuid4())]
        )
        with ActingAs(laid.caller):
            return await adapter.batch_load_by_ids(asked)


@dataclass(frozen=True)
class OneNodeAndTwoRefused(Then[SomeFragmentsAndACaller, Loaded]):
    """첫째는 노드, 둘째와 셋째는 그 항목만 거부된다."""

    @override
    def says(self) -> str:
        return Says(
            "자기 것은 노드, 남의 것과 없는 id 는 그 항목만 거부됩니다",
            english=(
                "the user's own comes back as a node, and another user's and the missing id "
                "are rejected for that item alone"
            ),
        )

    @override
    def look(self, laid: SomeFragmentsAndACaller, answered: Answered[Loaded]) -> list[Verdict]:
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
                SameAs[object](
                    laid.mine[0].id,
                    Says(
                        "미리 저장한 자기 조각",
                        english="the user's own fragment made in advance",
                    ),
                ),
            ),
            Refused(NotEnoughPermission, second if isinstance(second, BaseException) else None),
            Refused(NotEnoughPermission, third if isinstance(third, BaseException) else None),
        ]


@dataclass(frozen=True)
class TwoNodesOneMissing(Then[SomeFragmentsAndACaller, Loaded]):
    """둘은 노드, 셋째는 빈 항목."""

    @override
    def says(self) -> str:
        return Says(
            "있는 둘은 노드로 반환되고, 없는 id 에 해당하는 항목은 비어 있습니다",
            english=(
                "the two existing items come back as nodes and the item for the missing id is empty"
            ),
        )

    @override
    def look(self, laid: SomeFragmentsAndACaller, answered: Answered[Loaded]) -> list[Verdict]:
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
                    laid.mine[0].id,
                    Says(
                        "미리 저장한 자기 조각",
                        english="the user's own fragment made in advance",
                    ),
                ),
            ),
            Held[object](
                "items[1].id",
                getattr(items[1], "id", items[1]),
                SameAs[object](
                    laid.theirs.id,
                    Says(
                        "미리 저장한 남의 조각",
                        english="another user's fragment made in advance",
                    ),
                ),
            ),
            Same("items[2]", items[2], None),
        ]


@dataclass(frozen=True)
class NothingIsAnswered(Then[SomeFragmentsAndACaller, Loaded]):
    """빈 응답."""

    @override
    def says(self) -> str:
        return Says("빈 응답이 반환됩니다", english="an empty answer comes back")

    @override
    def look(self, laid: SomeFragmentsAndACaller, answered: Answered[Loaded]) -> list[Verdict]:
        items = answered.response
        if items is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        return [Same("items", list(items), [])]


@dataclass(frozen=True)
class MixedIdsAreAnsweredEach(
    Scenario[TestSeedingSession, SomeFragmentsAndACaller, AppConfigFragmentAdapter, Loaded]
):
    @override
    def summary(self) -> str:
        return "mine-anothers-and-a-missing-id-are-each-answered-in-order-for-a-plain-user"

    @override
    def describe(self) -> str:
        return Says(
            "자기 스코프에만 읽기 권한을 받은 사용자가 자기 조각, 다른 사용자의 조각, 없는 id 를 "
            "한 번에 조회하면, 목록 순서대로 자기 것은 노드, 남의 것과 없는 id 는 그 항목만 권한 "
            "부족으로 거부됩니다",
            english=(
                "when a user granted read permission only on their own scope reads their own "
                "fragment, another user's fragment and a missing id at once, in list order the "
                "own one comes back as a node and the others are rejected for that item alone "
                "for lack of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, SomeFragmentsAndACaller]:
        return SomeFragmentsAndSomeone(granted=(Permission.READ,))

    @override
    def when(self) -> When[SomeFragmentsAndACaller, AppConfigFragmentAdapter, Loaded]:
        return LoadingByIds()

    @override
    def then(self) -> Then[SomeFragmentsAndACaller, Loaded]:
        return OneNodeAndTwoRefused()


@dataclass(frozen=True)
class TheSuperadminSeesBoth(
    Scenario[TestSeedingSession, SomeFragmentsAndACaller, AppConfigFragmentAdapter, Loaded]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-reads-both-and-a-missing-id-comes-back-empty"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 조각 둘과 없는 id 하나를 한 번에 조회하면, 둘은 노드로 반환되고 "
            "없는 id 에 해당하는 항목은 비어 있습니다. 권한 검사를 통과하는 사용자만 빈 항목을 봅니다",
            english=(
                "when the superadmin reads two fragments and one missing id at once, the two "
                "come back as nodes and the item for the missing id is empty. Only a user who "
                "passes the permission check sees an empty item"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, SomeFragmentsAndACaller]:
        return SomeFragmentsAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[SomeFragmentsAndACaller, AppConfigFragmentAdapter, Loaded]:
        return LoadingByIds()

    @override
    def then(self) -> Then[SomeFragmentsAndACaller, Loaded]:
        return TwoNodesOneMissing()


@dataclass(frozen=True)
class AnEmptyListAnswersEmpty(
    Scenario[TestSeedingSession, SomeFragmentsAndACaller, AppConfigFragmentAdapter, Loaded]
):
    @override
    def summary(self) -> str:
        return "an-empty-id-list-answers-empty-without-calling-anything"

    @override
    def describe(self) -> str:
        return Says(
            "빈 id 목록을 주면 빈 응답이 반환됩니다. 하위 계층을 호출하지 않습니다",
            english="an empty id list answers empty without calling anything below",
        )

    @override
    def given(self) -> Given[TestSeedingSession, SomeFragmentsAndACaller]:
        return SomeFragmentsAndSomeone()

    @override
    def when(self) -> When[SomeFragmentsAndACaller, AppConfigFragmentAdapter, Loaded]:
        return LoadingByIds(nothing=True)

    @override
    def then(self) -> Then[SomeFragmentsAndACaller, Loaded]:
        return NothingIsAnswered()


SCENARIOS: list[LoadingStep] = [
    MixedIdsAreAnsweredEach(),
    TheSuperadminSeesBoth(),
    AnEmptyListAnswersEmpty(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_reading_many(
    scenario: LoadingStep, adapter: AppConfigFragmentAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
