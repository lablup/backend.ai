"""id 여럿으로 읽기 — 순서와 빈 자리, 그리고 권한이 없을 때."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

import pytest
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.container_registry import (
    NOTHING,
    ManyRegistriesAndACaller,
    ManyRegistriesAndSomeone,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

from ai.backend.common.data.entity.container_registry import ContainerRegistryID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.container_registry.response import ContainerRegistryNode
from ai.backend.manager.api.adapters.container_registry.adapter import ContainerRegistryAdapter
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Refused,
    Same,
    Scenario,
    Then,
    Verdict,
    When,
)

type Loaded = list[ContainerRegistryNode | None]
type ReadingStep = Scenario[
    SeedingSession, ManyRegistriesAndACaller, ContainerRegistryAdapter, Loaded
]


@dataclass(frozen=True)
class Loading(When[ManyRegistriesAndACaller, ContainerRegistryAdapter, Loaded]):
    """id 목록으로 한 번에 읽는다."""

    with_no_ids: bool = False

    @override
    def operation(self) -> str:
        return "batch_load_by_ids"

    @override
    def describe(self, laid: ManyRegistriesAndACaller) -> str:
        who = laid.caller.username
        if self.with_no_ids:
            return f"{who}이 빈 id 목록으로 읽음"
        return f"{who}이 심은 것 둘과 없는 id 하나를 한 번에 읽음"

    def _ids(self, laid: ManyRegistriesAndACaller) -> list[ContainerRegistryID]:
        if self.with_no_ids:
            return []
        return [
            ContainerRegistryID(laid.laid[0].id),
            ContainerRegistryID(NOTHING),
            ContainerRegistryID(laid.laid[1].id),
        ]

    @override
    async def call(
        self, adapter: ContainerRegistryAdapter, laid: ManyRegistriesAndACaller
    ) -> Loaded:
        with ActingAs(laid.caller):
            return await adapter.batch_load_by_ids(self._ids(laid))


@dataclass(frozen=True)
class TheOrderIsKeptAndTheHoleIsEmpty(Then[ManyRegistriesAndACaller, Loaded]):
    """준 순서 그대로 오고, 없는 id 자리는 비어서 온다."""

    @override
    def says(self) -> str:
        return "준 순서 그대로 오고 없는 id 자리는 비어 있다"

    @override
    def look(self, laid: ManyRegistriesAndACaller, answered: Answered[Loaded]) -> list[Verdict]:
        got = answered.response
        if got is None:
            return [
                Refused(type(answered.raised) if answered.raised else Exception, answered.raised)
            ]
        return [
            Same("length", len(got), 3),
            Same(
                "names",
                [one.registry_name if one is not None else None for one in got],
                [laid.laid[0].registry_name, None, laid.laid[1].registry_name],
            ),
        ]


@dataclass(frozen=True)
class AnEmptyListComesBack(Then[ManyRegistriesAndACaller, Loaded]):
    """빈 목록을 주면 빈 답이 온다."""

    @override
    def says(self) -> str:
        return "빈 답이 온다"

    @override
    def look(self, laid: ManyRegistriesAndACaller, answered: Answered[Loaded]) -> list[Verdict]:
        got = answered.response
        if got is None:
            return [
                Refused(type(answered.raised) if answered.raised else Exception, answered.raised)
            ]
        return [Same("items", got, [])]


@dataclass(frozen=True)
class LoadingKeepsTheOrderAndLeavesHoles(
    Scenario[SeedingSession, ManyRegistriesAndACaller, ContainerRegistryAdapter, Loaded]
):
    @override
    def summary(self) -> str:
        return "loading-many-ids-keeps-the-order-and-leaves-a-hole-for-a-missing-one"

    @override
    def describe(self) -> str:
        return (
            "슈퍼관리자가 심은 레지스트리 둘과 아무것도 갖지 않은 id 하나를 한 번에 읽으면, "
            "준 순서 그대로 오고 없는 id 자리만 비어서 온다"
        )

    @override
    def given(self) -> Given[SeedingSession, ManyRegistriesAndACaller]:
        return ManyRegistriesAndSomeone()

    @override
    def when(self) -> When[ManyRegistriesAndACaller, ContainerRegistryAdapter, Loaded]:
        return Loading()

    @override
    def then(self) -> Then[ManyRegistriesAndACaller, Loaded]:
        return TheOrderIsKeptAndTheHoleIsEmpty()


@dataclass(frozen=True)
class AnEmptyListAsksNothing(
    Scenario[SeedingSession, ManyRegistriesAndACaller, ContainerRegistryAdapter, Loaded]
):
    @override
    def summary(self) -> str:
        return "an-empty-id-list-answers-empty-without-calling-the-wiring"

    @override
    def describe(self) -> str:
        return "빈 id 목록으로 읽으면 배선을 부르지 않고 빈 답이 온다"

    @override
    def given(self) -> Given[SeedingSession, ManyRegistriesAndACaller]:
        return ManyRegistriesAndSomeone()

    @override
    def when(self) -> When[ManyRegistriesAndACaller, ContainerRegistryAdapter, Loaded]:
        return Loading(with_no_ids=True)

    @override
    def then(self) -> Then[ManyRegistriesAndACaller, Loaded]:
        return AnEmptyListComesBack()


@dataclass(frozen=True)
class APlainUserIsRefusedWholesale(
    Scenario[SeedingSession, ManyRegistriesAndACaller, ContainerRegistryAdapter, Loaded]
):
    @override
    def summary(self) -> str:
        return "a-plain-user-loading-many-ids-is-refused-as-a-whole"

    @override
    def describe(self) -> str:
        return (
            "슈퍼관리자가 아닌 사용자가 id 여럿을 한 번에 읽으려 하면, "
            "원소별로 갈리지 않고 요청 전체가 권한 부족으로 거부된다. "
            "이 호출은 id를 보기 전에 부른 사람이 슈퍼관리자인지부터 본다"
        )

    @override
    def given(self) -> Given[SeedingSession, ManyRegistriesAndACaller]:
        return ManyRegistriesAndSomeone(role=UserRole.USER)

    @override
    def when(self) -> When[ManyRegistriesAndACaller, ContainerRegistryAdapter, Loaded]:
        return Loading()

    @override
    def then(self) -> Then[ManyRegistriesAndACaller, Loaded]:
        return TheCallIsRefused(InsufficientPrivilege)


SCENARIOS: list[ReadingStep] = [
    LoadingKeepsTheOrderAndLeavesHoles(),
    AnEmptyListAsksNothing(),
    APlainUserIsRefusedWholesale(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_reading(
    scenario: ReadingStep,
    adapter: ContainerRegistryAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
