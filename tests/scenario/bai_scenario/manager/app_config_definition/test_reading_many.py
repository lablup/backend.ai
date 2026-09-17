"""여러 ID로 설정 정의 조회 — 원소마다 응답한다.

슈퍼관리자가 아니면 요청 전체가 막히는 것이 아니라 원소마다 거부된다. 없는 ID도 마찬가지로
거부 원소이고, 빈 항목으로 반환되는 것은 검사를 통과하는 슈퍼관리자에게뿐이다.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import override
from uuid import uuid4

import pytest

from ai.backend.common.data.entity.app_config_definition import AppConfigDefinitionID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.app_config_definition.response import (
    AppConfigDefinitionNode,
)
from ai.backend.manager.api.adapters.app_config_definition.adapter import (
    AppConfigDefinitionAdapter,
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
from bai_scenario.components.app_config_definition import (
    TwoDefinitionsAndACaller,
    TwoDefinitionsAndSomeone,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

type Loaded = list[AppConfigDefinitionNode | Exception | None]
type LoadingStep = Scenario[
    SeedingSession, TwoDefinitionsAndACaller, AppConfigDefinitionAdapter, Loaded
]


@dataclass(frozen=True)
class LoadingByIds(When[TwoDefinitionsAndACaller, AppConfigDefinitionAdapter, Loaded]):
    """여러 ID를 한 번에 조회한다."""

    nothing: bool = False
    duplicate_first: bool = False

    @override
    def operation(self) -> str:
        return "batch_load_by_ids"

    @override
    def describe(self, laid: TwoDefinitionsAndACaller) -> str:
        if self.nothing:
            return f"{laid.caller.username}이 빈 ID 목록으로 조회"
        if self.duplicate_first:
            return f"{laid.caller.username}이 첫 번째 설정 정의의 ID를 두 번 조회"
        return (
            f"{laid.caller.username}이 {laid.first.config_name}, {laid.second.config_name}, "
            "존재하지 않는 ID를 한 번에 조회"
        )

    @override
    async def call(
        self, adapter: AppConfigDefinitionAdapter, laid: TwoDefinitionsAndACaller
    ) -> Loaded:
        if self.nothing:
            asked = []
        elif self.duplicate_first:
            asked = [laid.first.id, laid.first.id]
        else:
            asked = [laid.first.id, laid.second.id, AppConfigDefinitionID(uuid4())]
        with ActingAs(laid.caller):
            return await adapter.batch_load_by_ids(asked)


@dataclass(frozen=True)
class EveryIdIsRefused(Then[TwoDefinitionsAndACaller, Loaded]):
    """세 항목 모두 그 항목만 거부된다."""

    @override
    def says(self) -> str:
        return "있는 둘도 없는 ID도 그 항목만 거부된다"

    @override
    def look(self, laid: TwoDefinitionsAndACaller, answered: Answered[Loaded]) -> list[Verdict]:
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
class TwoNodesOneMissing(Then[TwoDefinitionsAndACaller, Loaded]):
    """둘은 노드, 셋째는 빈 항목."""

    @override
    def says(self) -> str:
        return "있는 둘은 노드로 반환되고, 없는 ID에 해당하는 항목은 비어 있다"

    @override
    def look(self, laid: TwoDefinitionsAndACaller, answered: Answered[Loaded]) -> list[Verdict]:
        items = answered.response
        if items is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        seen: list[Verdict] = [Same("items", len(items), 3)]
        if len(items) != 3:
            return seen
        return [
            *seen,
            Held[object](
                "items[0].ID",
                getattr(items[0], "id", items[0]),
                SameAs[object](laid.first.id, "미리 만들어 둔 첫째 설정 정의"),
            ),
            Held[object](
                "items[1].ID",
                getattr(items[1], "id", items[1]),
                SameAs[object](laid.second.id, "미리 만들어 둔 둘째 설정 정의"),
            ),
            Same("items[2]", items[2], None),
        ]


@dataclass(frozen=True)
class NothingIsAnswered(Then[TwoDefinitionsAndACaller, Loaded]):
    """빈 응답."""

    @override
    def says(self) -> str:
        return "빈 응답이 반환된다"

    @override
    def look(self, laid: TwoDefinitionsAndACaller, answered: Answered[Loaded]) -> list[Verdict]:
        items = answered.response
        if items is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        return [Same("items", list(items), [])]


@dataclass(frozen=True)
class TheDuplicateIdKeepsBothPositions(Then[TwoDefinitionsAndACaller, Loaded]):
    """같은 ID를 두 번 요청하면 두 항목에 같은 노드가 반환된다."""

    @override
    def says(self) -> str:
        return "중복 ID의 두 항목에 같은 설정 정의가 반환된다"

    @override
    def look(self, laid: TwoDefinitionsAndACaller, answered: Answered[Loaded]) -> list[Verdict]:
        items = answered.response
        if items is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        seen: list[Verdict] = [Same("items", len(items), 2)]
        if len(items) != 2:
            return seen
        return [
            *seen,
            Held[object](
                "items[0].ID",
                getattr(items[0], "id", items[0]),
                SameAs[object](laid.first.id, "미리 만들어 둔 첫 번째 설정 정의"),
            ),
            Held[object](
                "items[1].ID",
                getattr(items[1], "id", items[1]),
                SameAs[object](laid.first.id, "미리 만들어 둔 첫 번째 설정 정의"),
            ),
        ]


@dataclass(frozen=True)
class APlainUserIsRefusedPerId(
    Scenario[SeedingSession, TwoDefinitionsAndACaller, AppConfigDefinitionAdapter, Loaded]
):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-is-refused-per-id"

    @override
    def describe(self) -> str:
        return (
            "슈퍼관리자가 아닌 사용자가 설정 정의 둘과 없는 ID 하나를 한 번에 조회하면, 요청 전체가 "
            "막히는 것이 아니라 세 항목 모두 그 항목만 권한 부족으로 거부된다"
        )

    @override
    def given(self) -> Given[SeedingSession, TwoDefinitionsAndACaller]:
        return TwoDefinitionsAndSomeone()

    @override
    def when(self) -> When[TwoDefinitionsAndACaller, AppConfigDefinitionAdapter, Loaded]:
        return LoadingByIds()

    @override
    def then(self) -> Then[TwoDefinitionsAndACaller, Loaded]:
        return EveryIdIsRefused()


@dataclass(frozen=True)
class TheSuperadminSeesBoth(
    Scenario[SeedingSession, TwoDefinitionsAndACaller, AppConfigDefinitionAdapter, Loaded]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-reads-both-and-a-missing-id-comes-back-empty"

    @override
    def describe(self) -> str:
        return (
            "슈퍼관리자가 설정 정의 둘과 없는 ID 하나를 한 번에 조회하면, 둘은 노드로 반환되고 없는 ID에 "
            "해당하는 항목은 비어 있다. 권한 검사를 통과하는 사용자만 빈 항목을 본다"
        )

    @override
    def given(self) -> Given[SeedingSession, TwoDefinitionsAndACaller]:
        return TwoDefinitionsAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[TwoDefinitionsAndACaller, AppConfigDefinitionAdapter, Loaded]:
        return LoadingByIds()

    @override
    def then(self) -> Then[TwoDefinitionsAndACaller, Loaded]:
        return TwoNodesOneMissing()


@dataclass(frozen=True)
class DuplicateIdsKeepTheirPositions(
    Scenario[SeedingSession, TwoDefinitionsAndACaller, AppConfigDefinitionAdapter, Loaded]
):
    @override
    def summary(self) -> str:
        return "duplicate-ids-keep-their-input-positions"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 같은 설정 정의 ID를 두 번 조회하면, 입력 순서를 보존해 같은 노드가 두 번 반환된다"

    @override
    def given(self) -> Given[SeedingSession, TwoDefinitionsAndACaller]:
        return TwoDefinitionsAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[TwoDefinitionsAndACaller, AppConfigDefinitionAdapter, Loaded]:
        return LoadingByIds(duplicate_first=True)

    @override
    def then(self) -> Then[TwoDefinitionsAndACaller, Loaded]:
        return TheDuplicateIdKeepsBothPositions()


@dataclass(frozen=True)
class AnEmptyListAnswersEmpty(
    Scenario[SeedingSession, TwoDefinitionsAndACaller, AppConfigDefinitionAdapter, Loaded]
):
    @override
    def summary(self) -> str:
        return "an-empty-id-list-answers-empty"

    @override
    def describe(self) -> str:
        return "빈 ID 목록을 주면 빈 응답이 반환된다"

    @override
    def given(self) -> Given[SeedingSession, TwoDefinitionsAndACaller]:
        return TwoDefinitionsAndSomeone()

    @override
    def when(self) -> When[TwoDefinitionsAndACaller, AppConfigDefinitionAdapter, Loaded]:
        return LoadingByIds(nothing=True)

    @override
    def then(self) -> Then[TwoDefinitionsAndACaller, Loaded]:
        return NothingIsAnswered()


SCENARIOS: list[LoadingStep] = [
    TheSuperadminSeesBoth(),
    DuplicateIdsKeepTheirPositions(),
    APlainUserIsRefusedPerId(),
    AnEmptyListAnswersEmpty(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_reading_many(
    scenario: LoadingStep, adapter: AppConfigDefinitionAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
