"""Shared contexts, inputs, and assertions for container registry scenarios."""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, override

from bai_scenario.components.answers import MissingResponse
from bai_scenario.components.domain import SomeoneOf
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.seeds.domain.domain import SeedDomain
from bai_scenario.seeds.image.registry import AllowProject, SeedContainerRegistry
from bai_scenario.seeds.project.project import SeedProject
from bai_scenario.seeds.rbac.role import SeedPermission, SeedRole
from bai_scenario.seeds.resource_policy.project import SeedProjectPolicy
from bai_scenario.seeds.seeder import Laid, Seeder, SeedNest

from ai.backend.common.container_registry import AllowedGroupsModel, ContainerRegistryType
from ai.backend.common.data.entity.container_registry import (
    ContainerRegistryEntityType,
    ContainerRegistryID,
)
from ai.backend.common.data.entity.project import ProjectEntityType, ProjectID
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.container_registry.request import AllowedGroupsInput
from ai.backend.common.dto.manager.v2.container_registry.response import ContainerRegistryNode
from ai.backend.manager.data.container_registry.types import ContainerRegistryData
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.data.project.types import ProjectData
from ai.backend.manager.data.user.types import UserData
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Same,
    Skipped,
    Then,
    Verdict,
)

MISSING_ENTITY_ID = uuid.UUID("00000000-0000-0000-0000-0000000000ff")
"""어떤 행에도 대응하지 않는 ID."""


@dataclass(frozen=True)
class AProjectAndACaller:
    project: ProjectData
    caller: UserData


@dataclass(frozen=True)
class ARegistryAndACaller:
    registry: ContainerRegistryData
    caller: UserData


@dataclass(frozen=True)
class ManyRegistriesAndACaller:
    """레지스트리 여러 개와 호출자. `matching_registry`는 검색 필터와 일치한다."""

    registries: tuple[ContainerRegistryData, ...]
    matching_registry: ContainerRegistryData
    caller: UserData


@dataclass(frozen=True)
class ARegistryToAllowAndACaller:
    registry: ContainerRegistryData
    project: ProjectData
    caller: UserData


@dataclass(frozen=True)
class NoRegistryYet(Given[SeedingSession, AProjectAndACaller]):
    role: UserRole = UserRole.USER

    @override
    def describe(self) -> str:
        return f"레지스트리 없음, 프로젝트 하나, 도메인 하나에 속한 {self.role.value} 한 명"

    @override
    async def lay(self, seeding: SeedingSession) -> AProjectAndACaller:
        domain = await seeding.creating(SeedDomain(name_hint="home"))
        policy = await seeding.once(SeedProjectPolicy())
        project = await seeding.creating_from_two(SeedProject(), domain, policy)
        caller = await seeding.within(SomeoneOf(domain, role=self.role))
        return AProjectAndACaller(seeding.made(project), seeding.made(caller))


@dataclass(frozen=True)
class ARegistryAndSomeone(Given[SeedingSession, ARegistryAndACaller]):
    role: UserRole = UserRole.USER
    name_hint: str = "host"
    allowed: bool = False

    @override
    def describe(self) -> str:
        allowed = ", 프로젝트 하나가 이미 허용돼 있음" if self.allowed else ""
        return f"레지스트리 하나, {self.role.value} 한 명{allowed}"

    @override
    async def lay(self, seeding: SeedingSession) -> ARegistryAndACaller:
        domain = await seeding.creating(SeedDomain(name_hint="home"))
        registry = await seeding.creating(SeedContainerRegistry(name_hint=self.name_hint))
        if self.allowed:
            policy = await seeding.once(SeedProjectPolicy())
            project = await seeding.creating_from_two(SeedProject(), domain, policy)
            await seeding.linking(AllowProject(), project, registry)
        caller = await seeding.within(SomeoneOf(domain, role=self.role))
        return ARegistryAndACaller(seeding.made(registry), seeding.made(caller))


@dataclass(frozen=True)
class ManyRegistriesAndSomeone(Given[SeedingSession, ManyRegistriesAndACaller]):
    role: UserRole = UserRole.SUPERADMIN
    besides: int = 1

    @override
    def describe(self) -> str:
        return f"레지스트리 {self.besides + 1}개, {self.role.value} 한 명"

    @override
    async def lay(self, seeding: SeedingSession) -> ManyRegistriesAndACaller:
        domain = await seeding.creating(SeedDomain(name_hint="home"))
        wanted = await seeding.creating(SeedContainerRegistry(name_hint="wanted"))
        others = [
            await seeding.creating(SeedContainerRegistry(name_hint="other"))
            for _ in range(self.besides)
        ]
        caller = await seeding.within(SomeoneOf(domain, role=self.role))
        return ManyRegistriesAndACaller(
            registries=tuple(seeding.made(one) for one in [wanted, *others]),
            matching_registry=seeding.made(wanted),
            caller=seeding.made(caller),
        )


@dataclass(frozen=True)
class ARegistryAndAProjectToAllow(Given[SeedingSession, ARegistryToAllowAndACaller]):
    """관계 동작은 지목한 스코프가 모두 허용해야 실행된다. 그래서 한쪽만 주는 자리가 필요하다."""

    role: UserRole = UserRole.USER
    on_registry: bool = True
    on_project: bool = True
    allowed: bool = False

    @override
    def describe(self) -> str:
        held = [
            place
            for place, given in (("레지스트리", self.on_registry), ("프로젝트", self.on_project))
            if given
        ]
        holds = ", ".join(held) + "에 권한 있음" if held else "아무 권한도 없음"
        already = ", 프로젝트는 이미 허용돼 있음" if self.allowed else ""
        return f"레지스트리 하나, 프로젝트 하나, {holds}인 사용자 한 명{already}"

    @override
    async def lay(self, seeding: SeedingSession) -> ARegistryToAllowAndACaller:
        domain = await seeding.creating(SeedDomain(name_hint="home"))
        policy = await seeding.once(SeedProjectPolicy())
        project = await seeding.creating_from_two(SeedProject(), domain, policy)
        registry = await seeding.creating(SeedContainerRegistry(name_hint="host"))
        if self.allowed:
            await seeding.linking(AllowProject(), project, registry)
        caller = await seeding.within(SomeoneOf(domain, role=self.role))
        if self.on_registry:
            await seeding.within(
                SomeoneAllowingIn(
                    registry,
                    caller,
                    scope_of=lambda one: ContainerRegistryID(one.id),
                    entity_type=ContainerRegistryEntityType(),
                    name_hint="allow-on-registry",
                )
            )
        if self.on_project:
            await seeding.within(
                SomeoneAllowingIn(
                    project,
                    caller,
                    scope_of=lambda one: ProjectID(one.id),
                    entity_type=ProjectEntityType(),
                    name_hint="allow-on-project",
                )
            )
        return ARegistryToAllowAndACaller(
            registry=seeding.made(registry),
            project=seeding.made(project),
            caller=seeding.made(caller),
        )


ALLOWING = (Permission.CREATE, Permission.SOFT_DELETE)
"""허용 목록에 넣고 빼는 데 드는 권한. 넣기는 생성이고 빼기는 삭제로 친다.

한 행이 한 비트만 담으므로 둘을 따로 심는다."""


@dataclass(frozen=True)
class SomeoneAllowingIn[ScopeData](SeedNest[Laid[None]]):
    """스코프 안에서 레지스트리 허용 목록을 수정할 역할을 사용자에게 부여한다."""

    scope: Laid[ScopeData]
    someone: Laid[UserData]
    scope_of: Callable[[ScopeData], EntityIdentifier]
    entity_type: EntityType
    name_hint: str

    @override
    def kind(self) -> str:
        return f"{self.name_hint} 권한을 받은 사용자 준비"

    @override
    def lay(self, seed: Seeder) -> Laid[None]:
        role = seed.creating_from(SeedRole(self.scope_of, name_hint=self.name_hint), self.scope)
        for allowed in ALLOWING:
            seed.adding(SeedPermission(entity_type=self.entity_type, permission=allowed), role)
        return seed.granting(
            role, self.someone, role_id=lambda r: r.id, user_id=lambda u: UserID(u.id)
        )


@dataclass(frozen=True)
class TheNewRegistryNode(Then[AProjectAndACaller, ContainerRegistryNode]):
    url: str
    registry_name: str
    registry_type: ContainerRegistryType = ContainerRegistryType.DOCKER
    project: str | None = None
    username: str | None = None
    ssl_verify: bool | None = True
    is_global: bool | None = True
    extra: dict[str, Any] | None = None

    @override
    def says(self) -> str:
        return "만든 레지스트리 전체가 온다"

    @override
    def look(
        self, laid: AProjectAndACaller, answered: Answered[ContainerRegistryNode]
    ) -> list[Verdict]:
        node = answered.response
        if node is None:
            return [MissingResponse(answered.raised)]
        return [
            Same("url", node.url, self.url),
            Same("registry_name", node.registry_name, self.registry_name),
            Same("type", node.type, self.registry_type),
            Same("project", node.project, self.project),
            Same("username", node.username, self.username),
            Same("ssl_verify", node.ssl_verify, self.ssl_verify),
            Same("is_global", node.is_global, self.is_global),
            Same("extra", node.extra, self.extra),
            Skipped("id", "데이터베이스가 만든다"),
        ]


@dataclass(frozen=True)
class TheUpdatedRegistryNode(Then[ARegistryAndACaller, ContainerRegistryNode]):
    url: str | None = None

    @override
    def says(self) -> str:
        return "심은 레지스트리 전체가 온다"

    @override
    def look(
        self, laid: ARegistryAndACaller, answered: Answered[ContainerRegistryNode]
    ) -> list[Verdict]:
        node = answered.response
        if node is None:
            return [MissingResponse(answered.raised)]
        if node.id != laid.registry.id:
            return [Same("id_matches_seeded_registry", node.id == laid.registry.id, True)]
        return [
            Same("url", node.url, self.url if self.url is not None else laid.registry.url),
            Same("registry_name", node.registry_name, laid.registry.registry_name),
            Same("type", node.type, laid.registry.type),
            Same("project", node.project, laid.registry.project),
            Same("username", node.username, laid.registry.username),
            Same("ssl_verify", node.ssl_verify, laid.registry.ssl_verify),
            Same("is_global", node.is_global, laid.registry.is_global),
            Same("extra", node.extra, laid.registry.extra),
            Skipped("id", "데이터베이스가 만든다"),
        ]


class RegistryTarget(ABC):
    """요청이 지목하는 레지스트리."""

    @abstractmethod
    def says(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def id_of(self, laid: ARegistryAndACaller) -> uuid.UUID:
        raise NotImplementedError


@dataclass(frozen=True)
class SeededRegistry(RegistryTarget):
    @override
    def says(self) -> str:
        return "심은 레지스트리"

    @override
    def id_of(self, laid: ARegistryAndACaller) -> uuid.UUID:
        return laid.registry.id


@dataclass(frozen=True)
class MissingRegistry(RegistryTarget):
    @override
    def says(self) -> str:
        return "아무것도 갖지 않은 id"

    @override
    def id_of(self, laid: ARegistryAndACaller) -> uuid.UUID:
        return MISSING_ENTITY_ID


class AllowedProjects(ABC):
    """만들기 요청이 허용 목록 자리에 담는 것."""

    @abstractmethod
    def says(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def of(self, laid: AProjectAndACaller) -> AllowedGroupsInput | None:
        raise NotImplementedError


@dataclass(frozen=True)
class NoProjects(AllowedProjects):
    @override
    def says(self) -> str:
        return "허용 목록 없이"

    @override
    def of(self, laid: AProjectAndACaller) -> AllowedGroupsInput | None:
        return None


@dataclass(frozen=True)
class SeededProject(AllowedProjects):
    @override
    def says(self) -> str:
        return "심은 프로젝트를 허용 목록에 넣고"

    @override
    def of(self, laid: AProjectAndACaller) -> AllowedGroupsInput:
        return AllowedGroupsInput(add=[str(laid.project.id)], remove=[])


@dataclass(frozen=True)
class MissingProject(AllowedProjects):
    @override
    def says(self) -> str:
        return "없는 프로젝트를 허용 목록에 넣고"

    @override
    def of(self, laid: AProjectAndACaller) -> AllowedGroupsInput:
        return AllowedGroupsInput(add=[str(MISSING_ENTITY_ID)], remove=[])


class AllowedProjectChange(ABC):
    """허용 목록을 고치는 요청이 한 방향으로 담는 것."""

    @abstractmethod
    def says(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def of(self, laid: ARegistryToAllowAndACaller) -> AllowedGroupsModel:
        raise NotImplementedError


@dataclass(frozen=True)
class AddProject(AllowedProjectChange):
    @override
    def says(self) -> str:
        return "허용 목록에 넣음"

    @override
    def of(self, laid: ARegistryToAllowAndACaller) -> AllowedGroupsModel:
        return AllowedGroupsModel(add=[str(laid.project.id)], remove=[])


@dataclass(frozen=True)
class RemoveProject(AllowedProjectChange):
    @override
    def says(self) -> str:
        return "허용 목록에서 뺌"

    @override
    def of(self, laid: ARegistryToAllowAndACaller) -> AllowedGroupsModel:
        return AllowedGroupsModel(add=[], remove=[str(laid.project.id)])


@dataclass(frozen=True)
class AddMissingProject(AllowedProjectChange):
    @override
    def says(self) -> str:
        return "없는 프로젝트를 허용 목록에 넣음"

    @override
    def of(self, laid: ARegistryToAllowAndACaller) -> AllowedGroupsModel:
        return AllowedGroupsModel(add=[str(MISSING_ENTITY_ID)], remove=[])
