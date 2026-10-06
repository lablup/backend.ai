"""Registry name lookup uses the resolved registry's read permission."""

from dataclasses import dataclass
from typing import override

import pytest

from ai.backend.common.data.entity.container_registry import ContainerRegistryID
from ai.backend.manager.api.adapters.container_registry.adapter import ContainerRegistryAdapter
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.errors.common import GenericBadRequest
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    SameAs,
    Scenario,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.answers import MissingResponse, TheCallIsRefused
from bai_scenario.components.container_registry import (
    ARegistryAndAProjectToAllow,
    ARegistryToAllowAndACaller,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario


@dataclass(frozen=True)
class LookingUp(When[ARegistryToAllowAndACaller, ContainerRegistryAdapter, ContainerRegistryID]):
    missing: bool = False

    @override
    def operation(self) -> str:
        return "lookup_by_name_and_project"

    @override
    def describe(self, laid: ARegistryToAllowAndACaller) -> str:
        return "일반 사용자가 이름과 프로젝트명으로 레지스트리 식별자를 조회"

    @override
    async def call(
        self, adapter: ContainerRegistryAdapter, laid: ARegistryToAllowAndACaller
    ) -> ContainerRegistryID:
        name = laid.registry.registry_name
        with ActingAs(laid.caller):
            return await adapter.lookup_by_name_and_project(
                f"{name}-missing" if self.missing else name, laid.registry.project
            )


@dataclass(frozen=True)
class TheRegistryIsResolved(Then[ARegistryToAllowAndACaller, ContainerRegistryID]):
    @override
    def says(self) -> str:
        return "준비한 레지스트리의 식별자가 반환된다"

    @override
    def look(
        self, laid: ARegistryToAllowAndACaller, answered: Answered[ContainerRegistryID]
    ) -> list[Verdict]:
        if answered.response is None:
            return [MissingResponse(answered.raised)]
        return [
            Held(
                "registry",
                answered.response,
                SameAs(ContainerRegistryID(laid.registry.id), "준비한 레지스트리"),
            )
        ]


@dataclass(frozen=True)
class LookupRegistry(
    Scenario[
        SeedingSession, ARegistryToAllowAndACaller, ContainerRegistryAdapter, ContainerRegistryID
    ]
):
    readable: bool = True
    missing: bool = False

    @override
    def summary(self) -> str:
        if self.missing:
            return "missing-registry-key-is-unresolvable"
        return (
            "readable-registry-key-resolves"
            if self.readable
            else "unreadable-registry-key-is-unresolvable"
        )

    @override
    def describe(self) -> str:
        if self.missing:
            return "존재하지 않는 이름은 읽기 권한이 없는 경우와 같은 오류로 거부된다"
        if self.readable:
            return "읽기 권한이 있는 사용자는 프로젝트명이 없는 레지스트리의 이름을 식별자로 변환할 수 있다"
        return "읽기 권한이 없는 사용자의 이름 조회는 대상의 존재 여부를 드러내지 않고 거부된다"

    @override
    def given(self) -> Given[SeedingSession, ARegistryToAllowAndACaller]:
        return ARegistryAndAProjectToAllow(
            on_registry=self.readable, on_project=False, permissions=(Permission.READ,)
        )

    @override
    def when(
        self,
    ) -> When[ARegistryToAllowAndACaller, ContainerRegistryAdapter, ContainerRegistryID]:
        return LookingUp(missing=self.missing)

    @override
    def then(self) -> Then[ARegistryToAllowAndACaller, ContainerRegistryID]:
        if self.missing or not self.readable:
            return TheCallIsRefused(GenericBadRequest)
        return TheRegistryIsResolved()


@pytest.mark.parametrize(
    "scenario",
    [LookupRegistry(), LookupRegistry(readable=False), LookupRegistry(missing=True)],
    ids=lambda scenario: scenario.summary(),
)
async def test_looking_up(
    scenario: LookupRegistry, adapter: ContainerRegistryAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
