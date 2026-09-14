"""허용 프로젝트 관계의 추가·제거와 권한 검사."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, override

import pytest
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.container_registry import (
    AddMissingProject,
    AddProject,
    AllowedProjectChange,
    ARegistryAndAProjectToAllow,
    ARegistryToAllowAndACaller,
    RemoveProject,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

from ai.backend.common.data.entity.container_registry import ContainerRegistryID
from ai.backend.common.data.user.types import UserRole
from ai.backend.manager.api.adapters.container_registry.adapter import ContainerRegistryAdapter
from ai.backend.manager.errors.image import ContainerRegistryGroupsAssociationNotFound
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.errors.resource import ProjectNotFound
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Configured,
    Given,
    Same,
    Scenario,
    Then,
    Verdict,
    When,
)

type AllowedProjectScenario = Scenario[
    SeedingSession, ARegistryToAllowAndACaller, ContainerRegistryAdapter, None
]


@dataclass(frozen=True)
class ChangingAllowedProjects(When[ARegistryToAllowAndACaller, ContainerRegistryAdapter, None]):
    change: AllowedProjectChange = field(default_factory=AddProject)

    @override
    def operation(self) -> str:
        return "apply_allowed_groups"

    @override
    def describe(self, laid: ARegistryToAllowAndACaller) -> str:
        return f"{laid.caller.username}이 {self.change.says()}"

    @override
    async def call(
        self, adapter: ContainerRegistryAdapter, laid: ARegistryToAllowAndACaller
    ) -> None:
        with ActingAs(laid.caller):
            await adapter.apply_allowed_groups(
                ContainerRegistryID(laid.registry.id), self.change.of(laid)
            )


@dataclass(frozen=True)
class TheCallReturnsNothing(Then[ARegistryToAllowAndACaller, None]):
    """반환값 없이 완료되는 호출의 성공 여부를 검사한다."""

    @override
    def says(self) -> str:
        return "답이 없고 예외도 없다"

    @override
    def look(self, laid: ARegistryToAllowAndACaller, answered: Answered[None]) -> list[Verdict]:
        if answered.raised is not None:
            return [Same("raised", answered.raised, None)]
        return [Same("response", answered.response, None)]


@dataclass(frozen=True)
class AddingProjectWithBothScopesGranted(
    Scenario[SeedingSession, ARegistryToAllowAndACaller, ContainerRegistryAdapter, None]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-on-both-scopes-allows-a-project-on-a-registry"

    @override
    def describe(self) -> str:
        return (
            "레지스트리와 프로젝트 두 스코프 모두에 권한을 받은 사용자는 "
            "그 프로젝트를 허용 목록에 넣을 수 있다"
        )

    @override
    def given(self) -> Given[SeedingSession, ARegistryToAllowAndACaller]:
        return ARegistryAndAProjectToAllow()

    @override
    def when(self) -> When[ARegistryToAllowAndACaller, ContainerRegistryAdapter, None]:
        return ChangingAllowedProjects()

    @override
    def then(self) -> Then[ARegistryToAllowAndACaller, None]:
        return TheCallReturnsNothing()


@dataclass(frozen=True)
class AddingExistingProjectIsIdempotent(
    Scenario[SeedingSession, ARegistryToAllowAndACaller, ContainerRegistryAdapter, None]
):
    @override
    def summary(self) -> str:
        return "allowing-a-project-that-is-already-allowed-is-not-an-error"

    @override
    def describe(self) -> str:
        return (
            "이미 허용된 프로젝트를 다시 허용 목록에 넣어도 거부되지 않는다. "
            "그 쌍은 데이터베이스에서 건너뛴다"
        )

    @override
    def given(self) -> Given[SeedingSession, ARegistryToAllowAndACaller]:
        return ARegistryAndAProjectToAllow(allowed=True)

    @override
    def when(self) -> When[ARegistryToAllowAndACaller, ContainerRegistryAdapter, None]:
        return ChangingAllowedProjects()

    @override
    def then(self) -> Then[ARegistryToAllowAndACaller, None]:
        return TheCallReturnsNothing()


@dataclass(frozen=True)
class RemovingAllowedProject(
    Scenario[SeedingSession, ARegistryToAllowAndACaller, ContainerRegistryAdapter, None]
):
    @override
    def summary(self) -> str:
        return "an-allowed-project-is-removed-from-the-allowed-list"

    @override
    def describe(self) -> str:
        return "이미 허용된 프로젝트는 허용 목록에서 뺄 수 있다"

    @override
    def given(self) -> Given[SeedingSession, ARegistryToAllowAndACaller]:
        return ARegistryAndAProjectToAllow(allowed=True)

    @override
    def when(self) -> When[ARegistryToAllowAndACaller, ContainerRegistryAdapter, None]:
        return ChangingAllowedProjects(change=RemoveProject())

    @override
    def then(self) -> Then[ARegistryToAllowAndACaller, None]:
        return TheCallReturnsNothing()


@dataclass(frozen=True)
class MissingProjectIsRefused(
    Scenario[SeedingSession, ARegistryToAllowAndACaller, ContainerRegistryAdapter, None]
):
    @override
    def summary(self) -> str:
        return "a-superadmin-naming-a-project-that-does-not-exist-is-refused"

    @override
    def describe(self) -> str:
        return (
            "존재하지 않는 프로젝트를 허용 목록에 넣으려 하면 그 프로젝트가 없다는 이유로 거부된다"
        )

    @override
    def given(self) -> Given[SeedingSession, ARegistryToAllowAndACaller]:
        return ARegistryAndAProjectToAllow(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ARegistryToAllowAndACaller, ContainerRegistryAdapter, None]:
        return ChangingAllowedProjects(change=AddMissingProject())

    @override
    def then(self) -> Then[ARegistryToAllowAndACaller, None]:
        return TheCallIsRefused(ProjectNotFound)


@dataclass(frozen=True)
class RemovingUnlinkedProjectIsRefused(
    Scenario[SeedingSession, ARegistryToAllowAndACaller, ContainerRegistryAdapter, None]
):
    @override
    def summary(self) -> str:
        return "a-superadmin-removing-a-project-that-was-never-allowed-is-refused"

    @override
    def describe(self) -> str:
        return "지목한 프로젝트 중 실제로 허용된 것이 하나도 없으면, 뺄 것이 없다는 이유로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, ARegistryToAllowAndACaller]:
        return ARegistryAndAProjectToAllow(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ARegistryToAllowAndACaller, ContainerRegistryAdapter, None]:
        return ChangingAllowedProjects(change=RemoveProject())

    @override
    def then(self) -> Then[ARegistryToAllowAndACaller, None]:
        return TheCallIsRefused(ContainerRegistryGroupsAssociationNotFound)


@dataclass(frozen=True)
class MissingProjectPermissionIsRefused(
    Scenario[SeedingSession, ARegistryToAllowAndACaller, ContainerRegistryAdapter, None]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-on-the-registry-but-not-the-project-is-refused"

    @override
    def describe(self) -> str:
        return (
            "레지스트리에만 권한을 받고 프로젝트에는 받지 못한 사용자가 프로젝트를 허용하려 하면, "
            "관계 동작은 지목한 스코프를 모두 보므로 권한 부족으로 막힌다"
        )

    @override
    def given(self) -> Given[SeedingSession, ARegistryToAllowAndACaller]:
        return ARegistryAndAProjectToAllow(on_project=False)

    @override
    def when(self) -> When[ARegistryToAllowAndACaller, ContainerRegistryAdapter, None]:
        return ChangingAllowedProjects()

    @override
    def then(self) -> Then[ARegistryToAllowAndACaller, None]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class DisabledEnforcementAllowsProject(
    Scenario[SeedingSession, ARegistryToAllowAndACaller, ContainerRegistryAdapter, None],
    Configured,
):
    @override
    def summary(self) -> str:
        return "turning-enforcement-off-lets-an-ungranted-user-allow-a-project"

    @override
    def describe(self) -> str:
        return (
            "엔티티 권한 집행을 끄면 아무 권한도 받지 않은 사용자도 프로젝트를 허용할 수 있다. "
            "이 문은 역할이 아니라 권한 그래프가 지키기 때문이다"
        )

    @override
    def config(self) -> Mapping[str, Any]:
        return {"manager.rbac.enforcement_enabled": False}

    @override
    def given(self) -> Given[SeedingSession, ARegistryToAllowAndACaller]:
        return ARegistryAndAProjectToAllow(on_registry=False, on_project=False)

    @override
    def when(self) -> When[ARegistryToAllowAndACaller, ContainerRegistryAdapter, None]:
        return ChangingAllowedProjects()

    @override
    def then(self) -> Then[ARegistryToAllowAndACaller, None]:
        return TheCallReturnsNothing()


SCENARIOS: list[AllowedProjectScenario] = [
    AddingProjectWithBothScopesGranted(),
    AddingExistingProjectIsIdempotent(),
    RemovingAllowedProject(),
    MissingProjectIsRefused(),
    RemovingUnlinkedProjectIsRefused(),
    MissingProjectPermissionIsRefused(),
    DisabledEnforcementAllowsProject(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_allowing_projects(
    scenario: AllowedProjectScenario,
    adapter: ContainerRegistryAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
