"""레지스트리 만들기 — 누가 만들 수 있고, 무엇이 만들기를 막는가."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, override

import pytest
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.container_registry import (
    ACallerWithNoRegistry,
    AllowedGroups,
    AProjectThatIsGone,
    ARegistryAndAProjectToAllow,
    ARegistryToAllowAndACaller,
    NoProjects,
    NoRegistryYet,
    TheLaidProject,
    TheNewRegistryNode,
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

ENFORCEMENT = "manager.rbac.enforcement_enabled"
A_URL = "https://made.scenario.local"
A_NAME = "made-registry"
NO_HOST = "http://"

type CreatingStep = Scenario[SeedingSession, Any, ContainerRegistryAdapter, ContainerRegistryNode]


@dataclass(frozen=True)
class Creating(When[Any, ContainerRegistryAdapter, ContainerRegistryNode]):
    """레지스트리를 만든다. 허용 프로젝트를 주면 연결까지 함께 쓴다."""

    url: str = A_URL
    username: str | None = None
    password: str | None = None
    allowed: AllowedGroups = field(default_factory=NoProjects)

    @override
    def operation(self) -> str:
        return "admin_create"

    @override
    def describe(self, laid: Any) -> str:
        return f"{laid.caller.username}이 {self.allowed.says()} {self.url}로 만듦"

    @override
    async def call(self, adapter: ContainerRegistryAdapter, laid: Any) -> ContainerRegistryNode:
        with ActingAs(laid.caller):
            payload = await adapter.admin_create(
                CreateContainerRegistryInput(
                    url=self.url,
                    registry_name=A_NAME,
                    type=ContainerRegistryType.DOCKER,
                    username=self.username,
                    password=self.password,
                    allowed_groups=self.allowed.of(laid),
                )
            )
        return payload.registry


@dataclass(frozen=True)
class CreatingWithOnlyTheRequiredValues(
    Scenario[SeedingSession, ACallerWithNoRegistry, ContainerRegistryAdapter, ContainerRegistryNode]
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
    def given(self) -> Given[SeedingSession, ACallerWithNoRegistry]:
        return NoRegistryYet(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[Any, ContainerRegistryAdapter, ContainerRegistryNode]:
        return Creating()

    @override
    def then(self) -> Then[Any, ContainerRegistryNode]:
        return TheNewRegistryNode(url=A_URL, registry_name=A_NAME)


@dataclass(frozen=True)
class CreatingWithAPasswordHidesIt(
    Scenario[SeedingSession, ACallerWithNoRegistry, ContainerRegistryAdapter, ContainerRegistryNode]
):
    @override
    def summary(self) -> str:
        return "a-password-given-at-creation-does-not-come-back-in-the-answer"

    @override
    def describe(self) -> str:
        return (
            "슈퍼관리자가 계정과 비밀번호를 함께 주고 만들면, "
            "계정 이름은 답에 실리지만 비밀번호 자리는 노드에 아예 없다"
        )

    @override
    def given(self) -> Given[SeedingSession, ACallerWithNoRegistry]:
        return NoRegistryYet(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[Any, ContainerRegistryAdapter, ContainerRegistryNode]:
        return Creating(username="someone", password="a-secret")

    @override
    def then(self) -> Then[Any, ContainerRegistryNode]:
        return TheNewRegistryNode(url=A_URL, registry_name=A_NAME, username="someone")


@dataclass(frozen=True)
class CreatingTakesAnAddressTheUpdateWouldRefuse(
    Scenario[SeedingSession, ACallerWithNoRegistry, ContainerRegistryAdapter, ContainerRegistryNode]
):
    @override
    def summary(self) -> str:
        return "an-address-the-update-path-would-refuse-still-creates-a-registry"

    @override
    def describe(self) -> str:
        return (
            "호스트가 없는 주소로도 레지스트리가 만들어진다. "
            "주소 검사는 고치는 경로에만 있고 만드는 경로에는 없기 때문이다"
        )

    @override
    def given(self) -> Given[SeedingSession, ACallerWithNoRegistry]:
        return NoRegistryYet(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[Any, ContainerRegistryAdapter, ContainerRegistryNode]:
        return Creating(url=NO_HOST)

    @override
    def then(self) -> Then[Any, ContainerRegistryNode]:
        return TheNewRegistryNode(url=NO_HOST, registry_name=A_NAME)


@dataclass(frozen=True)
class AllowingAProjectWhileCreating(
    Scenario[
        SeedingSession, ARegistryToAllowAndACaller, ContainerRegistryAdapter, ContainerRegistryNode
    ]
):
    @override
    def summary(self) -> str:
        return "a-project-named-while-creating-is-linked-to-the-new-registry"

    @override
    def describe(self) -> str:
        return (
            "슈퍼관리자는 허용 프로젝트를 함께 주고 레지스트리를 만들 수 있다. "
            "연결이 함께 쓰이는 것은 답에 실리지 않아 이 행이 보지 못한다"
        )

    @override
    def given(self) -> Given[SeedingSession, ARegistryToAllowAndACaller]:
        return ARegistryAndAProjectToAllow(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[Any, ContainerRegistryAdapter, ContainerRegistryNode]:
        return Creating(allowed=TheLaidProject())

    @override
    def then(self) -> Then[Any, ContainerRegistryNode]:
        return TheNewRegistryNode(url=A_URL, registry_name=A_NAME)


@dataclass(frozen=True)
class AProjectThatIsNotThereIsRefused(
    Scenario[
        SeedingSession, ARegistryToAllowAndACaller, ContainerRegistryAdapter, ContainerRegistryNode
    ]
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
    def given(self) -> Given[SeedingSession, ARegistryToAllowAndACaller]:
        return ARegistryAndAProjectToAllow(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[Any, ContainerRegistryAdapter, ContainerRegistryNode]:
        return Creating(allowed=AProjectThatIsGone())

    @override
    def then(self) -> Then[Any, ContainerRegistryNode]:
        return TheCallIsRefused(ProjectNotFound)


@dataclass(frozen=True)
class APlainUserMayNotCreate(
    Scenario[SeedingSession, ACallerWithNoRegistry, ContainerRegistryAdapter, ContainerRegistryNode]
):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-may-not-create-a-registry"

    @override
    def describe(self) -> str:
        return (
            "슈퍼관리자가 아닌 사용자가 레지스트리를 만들려 하면, "
            "권한을 얼마나 받았는지와 무관하게 역할로 막힌다"
        )

    @override
    def given(self) -> Given[SeedingSession, ACallerWithNoRegistry]:
        return NoRegistryYet()

    @override
    def when(self) -> When[Any, ContainerRegistryAdapter, ContainerRegistryNode]:
        return Creating()

    @override
    def then(self) -> Then[Any, ContainerRegistryNode]:
        return TheCallIsRefused(InsufficientPrivilege)


@dataclass(frozen=True)
class EnforcementOffChangesNothing(
    Scenario[
        SeedingSession, ACallerWithNoRegistry, ContainerRegistryAdapter, ContainerRegistryNode
    ],
    Configured,
):
    @override
    def summary(self) -> str:
        return "turning-enforcement-off-still-does-not-let-a-user-create-a-registry"

    @override
    def describe(self) -> str:
        return (
            "엔티티 권한 집행을 꺼도 레지스트리 생성은 여전히 막힌다. "
            "이 문은 권한 그래프가 아니라 역할이 지키기 때문이다"
        )

    @override
    def config(self) -> Mapping[str, Any]:
        return {ENFORCEMENT: False}

    @override
    def given(self) -> Given[SeedingSession, ACallerWithNoRegistry]:
        return NoRegistryYet()

    @override
    def when(self) -> When[Any, ContainerRegistryAdapter, ContainerRegistryNode]:
        return Creating()

    @override
    def then(self) -> Then[Any, ContainerRegistryNode]:
        return TheCallIsRefused(InsufficientPrivilege)


SCENARIOS: list[CreatingStep] = [
    CreatingWithOnlyTheRequiredValues(),
    CreatingWithAPasswordHidesIt(),
    CreatingTakesAnAddressTheUpdateWouldRefuse(),
    AllowingAProjectWhileCreating(),
    AProjectThatIsNotThereIsRefused(),
    APlainUserMayNotCreate(),
    EnforcementOffChangesNothing(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_creating(
    scenario: CreatingStep,
    adapter: ContainerRegistryAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
