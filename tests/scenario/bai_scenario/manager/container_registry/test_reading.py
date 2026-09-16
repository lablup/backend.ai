"""여러 ID 조회의 순서, 누락 값, 권한 검사."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

import pytest

from ai.backend.common.data.entity.container_registry import ContainerRegistryID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.container_registry.response import ContainerRegistryNode
from ai.backend.manager.api.adapters.container_registry.adapter import ContainerRegistryAdapter
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Refused,
    Same,
    Scenario,
    Skipped,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.answers import MissingResponse
from bai_scenario.components.container_registry import (
    MISSING_ENTITY_ID,
    ManyRegistriesAndACaller,
    ManyRegistriesAndSomeone,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

type Loaded = list[ContainerRegistryNode | Exception | None]
type ReadingScenario = Scenario[
    SeedingSession, ManyRegistriesAndACaller, ContainerRegistryAdapter, Loaded
]


@dataclass(frozen=True)
class Loading(When[ManyRegistriesAndACaller, ContainerRegistryAdapter, Loaded]):
    empty: bool = False

    @override
    def operation(self) -> str:
        return "batch_load_by_ids"

    @override
    def describe(self, laid: ManyRegistriesAndACaller) -> str:
        who = laid.caller.username
        if self.empty:
            return f"{who}이 빈 id 목록으로 조회"
        return f"{who}이 미리 만들어 둔 레지스트리 둘과 존재하지 않는 id 하나를 한 번에 조회"

    def registry_ids(self, laid: ManyRegistriesAndACaller) -> list[ContainerRegistryID]:
        if self.empty:
            return []
        return [
            ContainerRegistryID(laid.registries[0].id),
            ContainerRegistryID(MISSING_ENTITY_ID),
            ContainerRegistryID(laid.registries[1].id),
        ]

    @override
    async def call(
        self, adapter: ContainerRegistryAdapter, laid: ManyRegistriesAndACaller
    ) -> Loaded:
        with ActingAs(laid.caller):
            return await adapter.batch_load_by_ids(self.registry_ids(laid))


def registry_name_of(one: ContainerRegistryNode | Exception | None) -> str | None:
    if isinstance(one, ContainerRegistryNode):
        return one.registry_name
    return type(one).__name__ if one is not None else None


@dataclass(frozen=True)
class TheOrderIsKept(Then[ManyRegistriesAndACaller, Loaded]):
    @override
    def says(self) -> str:
        return "미리 만들어 둔 레지스트리는 요청한 순서대로 반환되고, 존재하지 않는 id의 항목은 검사하지 않는다"

    @override
    def look(self, laid: ManyRegistriesAndACaller, answered: Answered[Loaded]) -> list[Verdict]:
        got = answered.response
        if got is None:
            return [MissingResponse(answered.raised)]
        if len(got) != 3:
            return [Same("length", len(got), 3)]
        return [
            Same("length", len(got), 3),
            Same("[0].registry_name", registry_name_of(got[0]), laid.registries[0].registry_name),
            Skipped("[1]", "존재하지 않는 id에 슈퍼관리자가 받는 응답은 아직 정해지지 않았다"),
            Same("[2].registry_name", registry_name_of(got[2]), laid.registries[1].registry_name),
        ]


@dataclass(frozen=True)
class EveryIdIsRefused(Then[ManyRegistriesAndACaller, Loaded]):
    @override
    def says(self) -> str:
        return "항목마다 권한 부족 거부가 담겨 반환된다"

    @override
    def look(self, laid: ManyRegistriesAndACaller, answered: Answered[Loaded]) -> list[Verdict]:
        got = answered.response
        if got is None:
            return [MissingResponse(answered.raised)]
        return [
            Same("length", len(got), 3),
            *[
                Refused(NotEnoughPermission, one if isinstance(one, Exception) else None)
                for one in got
            ],
        ]


@dataclass(frozen=True)
class AnEmptyListComesBack(Then[ManyRegistriesAndACaller, Loaded]):
    @override
    def says(self) -> str:
        return "빈 응답이 반환된다"

    @override
    def look(self, laid: ManyRegistriesAndACaller, answered: Answered[Loaded]) -> list[Verdict]:
        got = answered.response
        if got is None:
            return [MissingResponse(answered.raised)]
        return [Same("items", got, [])]


@dataclass(frozen=True)
class LoadingKeepsTheOrder(
    Scenario[SeedingSession, ManyRegistriesAndACaller, ContainerRegistryAdapter, Loaded]
):
    @override
    def summary(self) -> str:
        return "loading-many-ids-keeps-the-order"

    @override
    def describe(self) -> str:
        return (
            "슈퍼관리자가 미리 만들어 둔 레지스트리 둘과 존재하지 않는 id 하나를 한 번에 조회하면, "
            "미리 만들어 둔 레지스트리는 요청한 순서대로 반환된다. "
            "존재하지 않는 id의 항목에 무엇이 반환되는지는 아직 정해지지 않았다"
        )

    @override
    def given(self) -> Given[SeedingSession, ManyRegistriesAndACaller]:
        return ManyRegistriesAndSomeone()

    @override
    def when(self) -> When[ManyRegistriesAndACaller, ContainerRegistryAdapter, Loaded]:
        return Loading()

    @override
    def then(self) -> Then[ManyRegistriesAndACaller, Loaded]:
        return TheOrderIsKept()


@dataclass(frozen=True)
class AnEmptyListAsksNothing(
    Scenario[SeedingSession, ManyRegistriesAndACaller, ContainerRegistryAdapter, Loaded]
):
    @override
    def summary(self) -> str:
        return "an-empty-id-list-answers-empty-without-calling-the-wiring"

    @override
    def describe(self) -> str:
        return "빈 id 목록으로 조회하면 하위 계층을 호출하지 않고 빈 응답이 반환된다"

    @override
    def given(self) -> Given[SeedingSession, ManyRegistriesAndACaller]:
        return ManyRegistriesAndSomeone()

    @override
    def when(self) -> When[ManyRegistriesAndACaller, ContainerRegistryAdapter, Loaded]:
        return Loading(empty=True)

    @override
    def then(self) -> Then[ManyRegistriesAndACaller, Loaded]:
        return AnEmptyListComesBack()


@dataclass(frozen=True)
class APlainUserIsRefusedOnEveryId(
    Scenario[SeedingSession, ManyRegistriesAndACaller, ContainerRegistryAdapter, Loaded]
):
    @override
    def summary(self) -> str:
        return "a-plain-user-loading-many-ids-is-refused-on-every-id"

    @override
    def describe(self) -> str:
        return (
            "권한을 받지 않은 사용자가 id 여럿을 한 번에 조회하면, 요청 전체가 거부되는 대신 "
            "항목마다 권한 부족 거부가 담겨 반환된다. "
            "존재하지 않는 id도 같은 거부로 반환되어 있는지 없는지가 드러나지 않는다"
        )

    @override
    def given(self) -> Given[SeedingSession, ManyRegistriesAndACaller]:
        return ManyRegistriesAndSomeone(role=UserRole.USER)

    @override
    def when(self) -> When[ManyRegistriesAndACaller, ContainerRegistryAdapter, Loaded]:
        return Loading()

    @override
    def then(self) -> Then[ManyRegistriesAndACaller, Loaded]:
        return EveryIdIsRefused()


SCENARIOS: list[ReadingScenario] = [
    LoadingKeepsTheOrder(),
    AnEmptyListAsksNothing(),
    APlainUserIsRefusedOnEveryId(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_reading(
    scenario: ReadingScenario,
    adapter: ContainerRegistryAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
