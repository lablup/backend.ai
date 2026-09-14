"""컨테이너 레지스트리 생성 권한과 거부 조건."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, override

import pytest
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.container_registry import (
    AllowedProjects,
    AProjectAndACaller,
    MissingProject,
    NoProjects,
    NoRegistryYet,
    SeededProject,
    TheNewRegistryNode,
    allowed_project_count,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.container_registry.request import (
    CreateContainerRegistryInput,
)
from ai.backend.common.dto.manager.v2.container_registry.response import ContainerRegistryNode
from ai.backend.manager.api.adapters.container_registry.adapter import ContainerRegistryAdapter
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.errors.resource import ProjectNotFound
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Configured, Given, Scenario, Then, When

type CreationScenario = Scenario[
    SeedingSession, AProjectAndACaller, ContainerRegistryAdapter, ContainerRegistryNode
]


@dataclass(frozen=True)
class Creating(When[AProjectAndACaller, ContainerRegistryAdapter, ContainerRegistryNode]):
    url: str = "https://made.scenario.local"
    registry_name: str = "made-registry"
    allowed_projects: AllowedProjects = field(default_factory=NoProjects)

    @override
    def operation(self) -> str:
        return "admin_create"

    @override
    def describe(self, laid: AProjectAndACaller) -> str:
        return f"{laid.caller.username}이 {self.allowed_projects.says()} {self.url}로 만듦"

    @override
    async def call(
        self, adapter: ContainerRegistryAdapter, laid: AProjectAndACaller
    ) -> ContainerRegistryNode:
        with ActingAs(laid.caller):
            payload = await adapter.admin_create(
                CreateContainerRegistryInput(
                    url=self.url,
                    registry_name=self.registry_name,
                    type=ContainerRegistryType.DOCKER,
                    allowed_groups=self.allowed_projects.of(laid),
                )
            )
        return payload.registry


@dataclass(frozen=True)
class CreatingWithOnlyTheRequiredValues(
    Scenario[SeedingSession, AProjectAndACaller, ContainerRegistryAdapter, ContainerRegistryNode]
):
    @override
    def summary(self) -> str:
        return "creating-a-registry-with-only-the-required-values-leaves-the-rest-empty"

    @override
    def describe(self) -> str:
        return (
            "슈퍼관리자가 주소와 이름과 종류만 주고 레지스트리를 만들면, "
            "나머지 자리가 모두 비어 있는 노드가 답으로 온다"
        )

    @override
    def given(self) -> Given[SeedingSession, AProjectAndACaller]:
        return NoRegistryYet(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> Creating:
        return Creating()

    @override
    def then(self) -> Then[AProjectAndACaller, ContainerRegistryNode]:
        sent = self.when()
        return TheNewRegistryNode(url=sent.url, registry_name=sent.registry_name)


@dataclass(frozen=True)
class AllowingAProjectWhileCreating(
    Scenario[SeedingSession, AProjectAndACaller, ContainerRegistryAdapter, ContainerRegistryNode]
):
    @override
    def summary(self) -> str:
        return "a-project-named-while-creating-is-allowed-on-the-new-registry"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 허용 프로젝트를 함께 주고 레지스트리를 만들면 그 관계도 생성된다"

    @override
    def given(self) -> Given[SeedingSession, AProjectAndACaller]:
        return NoRegistryYet(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> Creating:
        return Creating(allowed_projects=SeededProject())

    @override
    def then(self) -> Then[AProjectAndACaller, ContainerRegistryNode]:
        sent = self.when()
        return TheNewRegistryNode(url=sent.url, registry_name=sent.registry_name)


@dataclass(frozen=True)
class AProjectThatIsNotThereIsRefused(
    Scenario[SeedingSession, AProjectAndACaller, ContainerRegistryAdapter, ContainerRegistryNode]
):
    @override
    def summary(self) -> str:
        return "a-project-that-does-not-exist-is-refused-while-creating"

    @override
    def describe(self) -> str:
        return (
            "허용 목록에 없는 프로젝트를 넣고 레지스트리를 만들려 하면, "
            "그 프로젝트가 없다는 이유로 거부된다"
        )

    @override
    def given(self) -> Given[SeedingSession, AProjectAndACaller]:
        return NoRegistryYet(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AProjectAndACaller, ContainerRegistryAdapter, ContainerRegistryNode]:
        return Creating(allowed_projects=MissingProject())

    @override
    def then(self) -> Then[AProjectAndACaller, ContainerRegistryNode]:
        return TheCallIsRefused(ProjectNotFound)


@dataclass(frozen=True)
class APlainUserMayNotCreate(
    Scenario[SeedingSession, AProjectAndACaller, ContainerRegistryAdapter, ContainerRegistryNode]
):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-may-not-create-a-registry"

    @override
    def describe(self) -> str:
        return (
            "슈퍼관리자가 아닌 사용자가 레지스트리를 만들려 하면 권한 부족으로 거부된다. "
            "이 호출은 부른 사람이 슈퍼관리자인지만 보고, 어떤 권한을 받았는지는 보지 않는다"
        )

    @override
    def given(self) -> Given[SeedingSession, AProjectAndACaller]:
        return NoRegistryYet()

    @override
    def when(self) -> When[AProjectAndACaller, ContainerRegistryAdapter, ContainerRegistryNode]:
        return Creating()

    @override
    def then(self) -> Then[AProjectAndACaller, ContainerRegistryNode]:
        return TheCallIsRefused(InsufficientPrivilege)


@dataclass(frozen=True)
class EnforcementOffChangesNothing(
    Scenario[SeedingSession, AProjectAndACaller, ContainerRegistryAdapter, ContainerRegistryNode],
    Configured,
):
    @override
    def summary(self) -> str:
        return "turning-enforcement-off-still-does-not-let-a-user-create-a-registry"

    @override
    def describe(self) -> str:
        return (
            "엔티티 권한 집행을 꺼도 슈퍼관리자가 아닌 사용자는 여전히 권한 부족으로 거부된다. "
            "집행 스위치는 권한 그래프만 끄고, 부른 사람이 슈퍼관리자인지 보는 검사는 그대로 남기 때문이다"
        )

    @override
    def config(self) -> Mapping[str, Any]:
        return {"manager.rbac.enforcement_enabled": False}

    @override
    def given(self) -> Given[SeedingSession, AProjectAndACaller]:
        return NoRegistryYet()

    @override
    def when(self) -> When[AProjectAndACaller, ContainerRegistryAdapter, ContainerRegistryNode]:
        return Creating()

    @override
    def then(self) -> Then[AProjectAndACaller, ContainerRegistryNode]:
        return TheCallIsRefused(InsufficientPrivilege)


SCENARIOS: list[CreationScenario] = [
    CreatingWithOnlyTheRequiredValues(),
    AllowingAProjectWhileCreating(),
    AProjectThatIsNotThereIsRefused(),
    APlainUserMayNotCreate(),
    EnforcementOffChangesNothing(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_creating(
    scenario: CreationScenario,
    adapter: ContainerRegistryAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
    expected_count = 1 if isinstance(scenario, AllowingAProjectWhileCreating) else 0
    assert await allowed_project_count(engine) == expected_count
