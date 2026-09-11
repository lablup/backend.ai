"""What a container registry scenario table says besides the call.

How the adapter is built lives in the tables' own conftest, and the rows a scenario
lays come from ``seeds``. This holds what is left: the types these tables are written
against, and the situations worth naming more than once.
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, override

from bai_scenario.components.domain import SomeoneOf
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
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.container_registry.request import AllowedGroupsInput
from ai.backend.common.dto.manager.v2.container_registry.response import ContainerRegistryNode
from ai.backend.manager.data.container_registry.types import ContainerRegistryData
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.data.project.types import ProjectData
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Refused,
    Same,
    Skipped,
    Then,
    Verdict,
)

NOTHING = uuid.UUID("00000000-0000-0000-0000-0000000000ff")
"""아무 행도 갖지 않는 id. 대상이 없을 때 무엇이 오는지 보려고 지목한다."""

SEEDED_TYPE = ContainerRegistryType.DOCKER
"""시드가 심는 레지스트리의 종류. 기대값으로 다시 쓰므로 한 자리에 둔다."""


@dataclass(frozen=True)
class ACallerWithNoRegistry:
    """부를 사람 하나. 레지스트리를 아직 하나도 심지 않은 자리에 쓴다."""

    caller: UserData


@dataclass(frozen=True)
class ARegistryAndACaller:
    """레지스트리 하나와, 그것을 부를 사람."""

    registry: ContainerRegistryData
    caller: UserData


@dataclass(frozen=True)
class ManyRegistriesAndACaller:
    """레지스트리 여럿과 부를 사람. `named`는 그중 골라낼 하나다."""

    laid: tuple[ContainerRegistryData, ...]
    named: ContainerRegistryData
    caller: UserData


@dataclass(frozen=True)
class ARegistryToAllowAndACaller:
    """레지스트리 하나, 프로젝트 하나, 그리고 부를 사람."""

    registry: ContainerRegistryData
    project: ProjectData
    caller: UserData


@dataclass(frozen=True)
class NoRegistryYet(Given[Any, ACallerWithNoRegistry]):
    """레지스트리는 없고, 부를 사람만 하나."""

    role: UserRole = UserRole.USER

    @override
    def describe(self) -> str:
        return f"레지스트리 없음, 도메인 하나에 속한 {self.role.value} 한 명"

    @override
    async def lay(self, seeding: Any) -> ACallerWithNoRegistry:
        domain = await seeding.creating(SeedDomain(name_hint="home"))
        caller = await seeding.within(SomeoneOf(domain, role=self.role))
        return ACallerWithNoRegistry(seeding.made(caller))


@dataclass(frozen=True)
class ARegistryAndSomeone(Given[Any, ARegistryAndACaller]):
    """레지스트리 하나와, 부를 사람 하나."""

    role: UserRole = UserRole.USER
    name_hint: str = "host"
    linked: bool = False

    @override
    def describe(self) -> str:
        allowed = ", 프로젝트 하나가 이미 허용돼 있음" if self.linked else ""
        return f"레지스트리 하나, {self.role.value} 한 명{allowed}"

    @override
    async def lay(self, seeding: Any) -> ARegistryAndACaller:
        domain = await seeding.creating(SeedDomain(name_hint="home"))
        registry = await seeding.creating(SeedContainerRegistry(name_hint=self.name_hint))
        if self.linked:
            policy = await seeding.once(SeedProjectPolicy())
            project = await seeding.creating_from_two(SeedProject(), domain, policy)
            await seeding.linking(AllowProject(), project, registry)
        caller = await seeding.within(SomeoneOf(domain, role=self.role))
        return ARegistryAndACaller(seeding.made(registry), seeding.made(caller))


@dataclass(frozen=True)
class ManyRegistriesAndSomeone(Given[Any, ManyRegistriesAndACaller]):
    """레지스트리 여럿과, 부를 사람 하나."""

    role: UserRole = UserRole.SUPERADMIN
    besides: int = 1

    @override
    def describe(self) -> str:
        return f"레지스트리 {self.besides + 1}개, {self.role.value} 한 명"

    @override
    async def lay(self, seeding: Any) -> ManyRegistriesAndACaller:
        domain = await seeding.creating(SeedDomain(name_hint="home"))
        wanted = await seeding.creating(SeedContainerRegistry(name_hint="wanted"))
        others = [
            await seeding.creating(SeedContainerRegistry(name_hint="other"))
            for _ in range(self.besides)
        ]
        caller = await seeding.within(SomeoneOf(domain, role=self.role))
        return ManyRegistriesAndACaller(
            laid=tuple(seeding.made(one) for one in [wanted, *others]),
            named=seeding.made(wanted),
            caller=seeding.made(caller),
        )


@dataclass(frozen=True)
class ARegistryAndAProjectToAllow(Given[Any, ARegistryToAllowAndACaller]):
    """레지스트리와 프로젝트, 그리고 두 스코프에 권한을 어디까지 받았는지 고른 사람.

    관계 동작은 지목한 스코프가 모두 허용해야 실행된다. 그래서 한쪽만 주는 자리가 필요하다.
    """

    role: UserRole = UserRole.USER
    on_registry: bool = True
    on_project: bool = True
    linked: bool = False

    @override
    def describe(self) -> str:
        held = [
            place
            for place, given in (("레지스트리", self.on_registry), ("프로젝트", self.on_project))
            if given
        ]
        holds = ", ".join(held) + "에 권한 있음" if held else "아무 권한도 없음"
        already = ", 둘은 이미 연결돼 있음" if self.linked else ""
        return f"레지스트리 하나, 프로젝트 하나, {holds}인 사용자 한 명{already}"

    @override
    async def lay(self, seeding: Any) -> ARegistryToAllowAndACaller:
        domain = await seeding.creating(SeedDomain(name_hint="home"))
        policy = await seeding.once(SeedProjectPolicy())
        project = await seeding.creating_from_two(SeedProject(), domain, policy)
        registry = await seeding.creating(SeedContainerRegistry(name_hint="host"))
        if self.linked:
            await seeding.linking(AllowProject(), project, registry)
        caller = await seeding.within(SomeoneOf(domain, role=self.role))
        if self.on_registry:
            await seeding.within(
                SomeoneLinkingIn(
                    registry,
                    caller,
                    scope_of=lambda one: ContainerRegistryID(one.id),
                    entity_type=ContainerRegistryEntityType(),
                    name_hint="registry-linker",
                )
            )
        if self.on_project:
            await seeding.within(
                SomeoneLinkingIn(
                    project,
                    caller,
                    scope_of=lambda one: ProjectID(one.id),
                    entity_type=ContainerRegistryEntityType(),
                    name_hint="project-linker",
                )
            )
        return ARegistryToAllowAndACaller(
            registry=seeding.made(registry),
            project=seeding.made(project),
            caller=seeding.made(caller),
        )


LINKING = (Permission.CREATE, Permission.SOFT_DELETE)
"""연결을 붙이고 떼는 데 드는 권한. 붙이기는 생성이고 떼기는 삭제로 친다.

한 행이 한 비트만 담으므로 둘을 따로 심는다."""


@dataclass(frozen=True)
class SomeoneLinkingIn[ScopeData](SeedNest[Laid[None]]):
    """그 스코프 안에서 레지스트리 연결을 다룰 수 있는 역할을 사용자에게 준다.

    관계 동작은 자기 엔티티 종류를 선언하지 않는다. 지목한 스코프마다 대상 엔티티 종류로
    권한을 묻기 때문에, 프로젝트 스코프에서도 레지스트리 종류로 적는다.
    """

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
        for allowed in LINKING:
            seed.adding(SeedPermission(entity_type=self.entity_type, permission=allowed), role)
        return seed.granting(
            role, self.someone, role_id=lambda r: r.id, user_id=lambda u: UserID(u.id)
        )


@dataclass(frozen=True)
class TheNewRegistryNode(Then[Any, ContainerRegistryNode]):
    """방금 만든 레지스트리가 통째로 온다. 시나리오가 정한 값만 여기로 받는다."""

    url: str
    registry_name: str
    kind: ContainerRegistryType = ContainerRegistryType.DOCKER
    project: str | None = None
    username: str | None = None
    ssl_verify: bool | None = True
    is_global: bool | None = True
    extra: dict[str, Any] | None = None

    @override
    def says(self) -> str:
        return "만든 레지스트리 전체가 온다"

    @override
    def look(self, laid: Any, answered: Answered[ContainerRegistryNode]) -> list[Verdict]:
        node = answered.response
        if node is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        return [
            Same("url", node.url, self.url),
            Same("registry_name", node.registry_name, self.registry_name),
            Same("type", node.type, self.kind),
            Same("project", node.project, self.project),
            Same("username", node.username, self.username),
            Same("ssl_verify", node.ssl_verify, self.ssl_verify),
            Same("is_global", node.is_global, self.is_global),
            Same("extra", node.extra, self.extra),
            Skipped("id", "데이터베이스가 만든다"),
        ]


@dataclass(frozen=True)
class TheRegistryNode(Then[ARegistryAndACaller, ContainerRegistryNode]):
    """심은 레지스트리가 통째로 온다. 시나리오가 바꾼 자리만 여기로 받는다."""

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
            return [Refused(EntityNotFoundError, answered.raised)]
        return [
            Same("url", node.url, self.url if self.url is not None else laid.registry.url),
            Same("registry_name", node.registry_name, laid.registry.registry_name),
            Same("type", node.type, SEEDED_TYPE),
            Same("project", node.project, laid.registry.project),
            Same("username", node.username, laid.registry.username),
            Same("ssl_verify", node.ssl_verify, laid.registry.ssl_verify),
            Same("is_global", node.is_global, laid.registry.is_global),
            Same("extra", node.extra, laid.registry.extra),
            Skipped("id", "데이터베이스가 만든다"),
        ]


class Target(ABC):
    """요청이 지목하는 레지스트리."""

    @abstractmethod
    def says(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def id_of(self, laid: ARegistryAndACaller) -> uuid.UUID:
        raise NotImplementedError


@dataclass(frozen=True)
class TheLaidRegistry(Target):
    """전제가 심어 둔 그 레지스트리."""

    @override
    def says(self) -> str:
        return "심은 레지스트리"

    @override
    def id_of(self, laid: ARegistryAndACaller) -> uuid.UUID:
        return laid.registry.id


@dataclass(frozen=True)
class AnIdThatHoldsNothing(Target):
    """아무 레지스트리도 갖지 않는 id."""

    @override
    def says(self) -> str:
        return "아무것도 갖지 않은 id"

    @override
    def id_of(self, laid: ARegistryAndACaller) -> uuid.UUID:
        return NOTHING


class AllowedGroups(ABC):
    """만들기 요청이 허용 목록 자리에 담는 것."""

    @abstractmethod
    def says(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def of(self, laid: Any) -> AllowedGroupsInput | None:
        raise NotImplementedError


@dataclass(frozen=True)
class NoProjects(AllowedGroups):
    """허용 목록을 아예 주지 않는다."""

    @override
    def says(self) -> str:
        return "허용 목록 없이"

    @override
    def of(self, laid: Any) -> AllowedGroupsInput | None:
        return None


@dataclass(frozen=True)
class TheLaidProject(AllowedGroups):
    """전제가 심어 둔 그 프로젝트를 허용한다."""

    @override
    def says(self) -> str:
        return "심은 프로젝트를 허용 목록에 넣고"

    @override
    def of(self, laid: Any) -> AllowedGroupsInput:
        return AllowedGroupsInput(add=[str(laid.project.id)], remove=[])


@dataclass(frozen=True)
class AProjectThatIsGone(AllowedGroups):
    """아무 프로젝트도 갖지 않는 id를 허용하려 한다."""

    @override
    def says(self) -> str:
        return "없는 프로젝트를 허용 목록에 넣고"

    @override
    def of(self, laid: Any) -> AllowedGroupsInput:
        return AllowedGroupsInput(add=[str(NOTHING)], remove=[])


class GroupChange(ABC):
    """허용 목록을 고치는 요청이 한 방향으로 담는 것."""

    @abstractmethod
    def says(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def of(self, laid: ARegistryToAllowAndACaller) -> AllowedGroupsModel:
        raise NotImplementedError


@dataclass(frozen=True)
class Adding(GroupChange):
    """그 프로젝트를 허용 목록에 넣는다."""

    @override
    def says(self) -> str:
        return "허용 목록에 넣음"

    @override
    def of(self, laid: ARegistryToAllowAndACaller) -> AllowedGroupsModel:
        return AllowedGroupsModel(add=[str(laid.project.id)], remove=[])


@dataclass(frozen=True)
class Removing(GroupChange):
    """그 프로젝트를 허용 목록에서 뺀다."""

    @override
    def says(self) -> str:
        return "허용 목록에서 뺌"

    @override
    def of(self, laid: ARegistryToAllowAndACaller) -> AllowedGroupsModel:
        return AllowedGroupsModel(add=[], remove=[str(laid.project.id)])


@dataclass(frozen=True)
class AddingWhatIsGone(GroupChange):
    """아무 프로젝트도 갖지 않는 id를 허용 목록에 넣으려 한다."""

    @override
    def says(self) -> str:
        return "없는 프로젝트를 허용 목록에 넣음"

    @override
    def of(self, laid: ARegistryToAllowAndACaller) -> AllowedGroupsModel:
        return AllowedGroupsModel(add=[str(NOTHING)], remove=[])
