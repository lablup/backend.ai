"""레지스트리 고치기 — 무엇이 바뀌고, 고친 뒤의 행이 무엇에 걸리는가."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import override

import pytest
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.container_registry import (
    AnIdThatHoldsNothing,
    ARegistryAndACaller,
    ARegistryAndSomeone,
    Target,
    TheLaidRegistry,
    TheRegistryNode,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.container_registry.request import (
    UpdateContainerRegistryInput,
)
from ai.backend.common.dto.manager.v2.container_registry.response import ContainerRegistryNode
from ai.backend.manager.api.adapters.container_registry.adapter import ContainerRegistryAdapter
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.errors.container_registry import (
    InvalidContainerRegistryProject,
    InvalidContainerRegistryURL,
)
from ai.backend.manager.errors.image import ContainerRegistryNotFound
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Scenario, Then, When

ANOTHER_URL = "https://moved.scenario.local"
NO_HOST = "http://"

type EditingStep = Scenario[
    SeedingSession, ARegistryAndACaller, ContainerRegistryAdapter, ContainerRegistryNode
]


@dataclass(frozen=True)
class Editing(When[ARegistryAndACaller, ContainerRegistryAdapter, ContainerRegistryNode]):
    """레지스트리를 고친다. 값을 하나도 주지 않으면 아무것도 바뀌지 않는다."""

    url: str | None = None
    kind: ContainerRegistryType | None = None
    project: str | None = None
    at: Target = field(default_factory=TheLaidRegistry)

    @override
    def operation(self) -> str:
        return "admin_update"

    @override
    def describe(self, laid: ARegistryAndACaller) -> str:
        who = laid.caller.username
        if isinstance(self.at, AnIdThatHoldsNothing):
            return f"{who}이 {self.at.says()}를 고침"
        if self.url is not None:
            return f"{who}이 주소를 {self.url}로 고침"
        if self.kind is not None:
            return f"{who}이 종류를 {self.kind.value}로 고침"
        return f"{who}이 아무 값도 주지 않고 고침"

    @override
    async def call(
        self, adapter: ContainerRegistryAdapter, laid: ARegistryAndACaller
    ) -> ContainerRegistryNode:
        target = self.at.id_of(laid)
        with ActingAs(laid.caller):
            payload = await adapter.admin_update(
                UpdateContainerRegistryInput(
                    id=target, url=self.url, type=self.kind, project=self.project
                )
            )
        return payload.registry


@dataclass(frozen=True)
class ChangingOnlyTheAddress(
    Scenario[SeedingSession, ARegistryAndACaller, ContainerRegistryAdapter, ContainerRegistryNode]
):
    @override
    def summary(self) -> str:
        return "changing-only-the-address-leaves-every-other-field-alone"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 주소만 고치면 주소만 새 값이 되고 나머지 자리는 그대로다"

    @override
    def given(self) -> Given[SeedingSession, ARegistryAndACaller]:
        return ARegistryAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ARegistryAndACaller, ContainerRegistryAdapter, ContainerRegistryNode]:
        return Editing(url=ANOTHER_URL)

    @override
    def then(self) -> Then[ARegistryAndACaller, ContainerRegistryNode]:
        return TheRegistryNode(url=ANOTHER_URL)


@dataclass(frozen=True)
class AnEmptyEditChangesNothing(
    Scenario[SeedingSession, ARegistryAndACaller, ContainerRegistryAdapter, ContainerRegistryNode]
):
    @override
    def summary(self) -> str:
        return "an-edit-that-names-no-value-changes-nothing"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 값을 하나도 주지 않고 고치면 아무것도 바뀌지 않은 노드가 온다"

    @override
    def given(self) -> Given[SeedingSession, ARegistryAndACaller]:
        return ARegistryAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ARegistryAndACaller, ContainerRegistryAdapter, ContainerRegistryNode]:
        return Editing()

    @override
    def then(self) -> Then[ARegistryAndACaller, ContainerRegistryNode]:
        return TheRegistryNode()


@dataclass(frozen=True)
class AnAddressWithoutAHostIsRefused(
    Scenario[SeedingSession, ARegistryAndACaller, ContainerRegistryAdapter, ContainerRegistryNode]
):
    @override
    def summary(self) -> str:
        return "an-address-whose-host-is-empty-is-refused-on-update"

    @override
    def describe(self) -> str:
        return (
            "슈퍼관리자가 호스트 자리가 비는 주소로 고치려 하면, "
            "고친 뒤의 행을 보는 검사가 주소 형식으로 막는다"
        )

    @override
    def given(self) -> Given[SeedingSession, ARegistryAndACaller]:
        return ARegistryAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ARegistryAndACaller, ContainerRegistryAdapter, ContainerRegistryNode]:
        return Editing(url=NO_HOST)

    @override
    def then(self) -> Then[ARegistryAndACaller, ContainerRegistryNode]:
        return TheCallIsRefused(InvalidContainerRegistryURL)


@dataclass(frozen=True)
class HarborWithoutAProjectIsRefused(
    Scenario[SeedingSession, ARegistryAndACaller, ContainerRegistryAdapter, ContainerRegistryNode]
):
    @override
    def summary(self) -> str:
        return "turning-a-registry-into-harbor-without-a-project-is-refused"

    @override
    def describe(self) -> str:
        return (
            "프로젝트가 비어 있는 레지스트리를 harbor 종류로 고치려 하면, "
            "harbor는 프로젝트를 요구하므로 그 값으로 막힌다"
        )

    @override
    def given(self) -> Given[SeedingSession, ARegistryAndACaller]:
        return ARegistryAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ARegistryAndACaller, ContainerRegistryAdapter, ContainerRegistryNode]:
        return Editing(kind=ContainerRegistryType.HARBOR2)

    @override
    def then(self) -> Then[ARegistryAndACaller, ContainerRegistryNode]:
        return TheCallIsRefused(InvalidContainerRegistryProject)


@dataclass(frozen=True)
class AnIdThatHoldsNothingIsRefused(
    Scenario[SeedingSession, ARegistryAndACaller, ContainerRegistryAdapter, ContainerRegistryNode]
):
    @override
    def summary(self) -> str:
        return "editing-an-id-that-holds-no-registry-is-refused"

    @override
    def describe(self) -> str:
        return "아무 레지스트리도 갖지 않은 id를 고치려 하면 대상이 없다는 이유로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, ARegistryAndACaller]:
        return ARegistryAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ARegistryAndACaller, ContainerRegistryAdapter, ContainerRegistryNode]:
        return Editing(url=ANOTHER_URL, at=AnIdThatHoldsNothing())

    @override
    def then(self) -> Then[ARegistryAndACaller, ContainerRegistryNode]:
        return TheCallIsRefused(ContainerRegistryNotFound)


@dataclass(frozen=True)
class APlainUserMayNotEdit(
    Scenario[SeedingSession, ARegistryAndACaller, ContainerRegistryAdapter, ContainerRegistryNode]
):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-may-not-edit-a-registry"

    @override
    def describe(self) -> str:
        return (
            "슈퍼관리자가 아닌 사용자가 레지스트리를 고치려 하면 권한 부족으로 거부된다. "
            "이 호출은 부른 사람이 슈퍼관리자인지만 보고, 어떤 권한을 받았는지는 보지 않는다"
        )

    @override
    def given(self) -> Given[SeedingSession, ARegistryAndACaller]:
        return ARegistryAndSomeone()

    @override
    def when(self) -> When[ARegistryAndACaller, ContainerRegistryAdapter, ContainerRegistryNode]:
        return Editing(url=ANOTHER_URL)

    @override
    def then(self) -> Then[ARegistryAndACaller, ContainerRegistryNode]:
        return TheCallIsRefused(InsufficientPrivilege)


SCENARIOS: list[EditingStep] = [
    ChangingOnlyTheAddress(),
    AnEmptyEditChangesNothing(),
    AnAddressWithoutAHostIsRefused(),
    HarborWithoutAProjectIsRefused(),
    AnIdThatHoldsNothingIsRefused(),
    APlainUserMayNotEdit(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_editing(
    scenario: EditingStep,
    adapter: ContainerRegistryAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
