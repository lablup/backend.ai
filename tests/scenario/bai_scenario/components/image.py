"""What an image scenario table says besides the call.

How the adapter is built lives in the tables' own conftest, and the rows a scenario
lays come from ``seeds``. This holds what is left: the types these tables are written
against, and the situations worth naming more than once.
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, override

from bai_scenario.components.domain import SomeoneOf
from bai_scenario.seeds.domain.domain import SeedDomain
from bai_scenario.seeds.image.image import SeedAlias, SeedImage
from bai_scenario.seeds.image.registry import SeedContainerRegistry
from bai_scenario.seeds.rbac.role import SeedPermission, SeedRole
from bai_scenario.seeds.seeder import Laid, Seeder, SeedNest

from ai.backend.common.data.entity.container_registry import ContainerRegistryID
from ai.backend.common.data.entity.image import ImageEntityType
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.image.response import ImageNode
from ai.backend.manager.data.container_registry.types import ContainerRegistryData
from ai.backend.manager.data.image.types import ImageAliasData, ImageData, ImageStatus
from ai.backend.manager.data.permission.types import Permission
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

REACHING = (Permission.READ, Permission.SOFT_DELETE, Permission.HARD_DELETE)
"""이미지를 읽고 잊고 지우는 데 드는 권한.

한 행이 한 비트만 담으므로 셋을 따로 심는다. 역할은 하나다."""


@dataclass(frozen=True)
class AnImageAndACaller:
    """이미지 하나와, 그것을 부를 사람."""

    image: ImageData
    caller: UserData


@dataclass(frozen=True)
class ManyImagesAndACaller:
    """이미지 여럿과 부를 사람. `named`는 그중 골라낼 하나다."""

    laid: tuple[ImageData, ...]
    named: ImageData
    registry: ContainerRegistryData
    caller: UserData


@dataclass(frozen=True)
class AnAliasAndACaller:
    """별칭이 붙은 이미지 하나와, 그것을 부를 사람."""

    image: ImageData
    alias: ImageAliasData
    caller: UserData


@dataclass(frozen=True)
class ARegistryWithImages(SeedNest[tuple[ContainerRegistryData, tuple[Laid[ImageData], ...]]]):
    """레지스트리 하나와 그 안의 이미지들. 이미지는 레지스트리에 붙어야 존재한다."""

    count: int = 1

    @override
    def kind(self) -> str:
        return "이미지를 담을 레지스트리 준비"

    @override
    def lay(self, seed: Seeder) -> tuple[Any, tuple[Laid[ImageData], ...]]:
        registry = seed.creating(SeedContainerRegistry(name_hint="host"))
        images = tuple(
            seed.creating_from(SeedImage(name_hint=f"image-{index}"), registry)
            for index in range(self.count)
        )
        return registry, images


@dataclass(frozen=True)
class AnImageAndSomeone(Given[Any, AnImageAndACaller]):
    """이미지 하나와, 부를 사람 하나."""

    role: UserRole = UserRole.USER
    status: ImageStatus = ImageStatus.ALIVE

    @override
    def describe(self) -> str:
        marked = "" if self.status is ImageStatus.ALIVE else f", 상태는 {self.status.value}"
        return f"레지스트리 하나와 그 안의 이미지 하나{marked}, {self.role.value} 한 명"

    @override
    async def lay(self, seeding: Any) -> AnImageAndACaller:
        domain = await seeding.creating(SeedDomain(name_hint="home"))
        registry = await seeding.creating(SeedContainerRegistry(name_hint="host"))
        image = await seeding.creating_from(SeedImage(status=self.status), registry)
        caller = await seeding.within(SomeoneOf(domain, role=self.role))
        return AnImageAndACaller(seeding.made(image), seeding.made(caller))


@dataclass(frozen=True)
class AnImageNobodyOwns(Given[Any, AnImageAndACaller]):
    """출하된 이미지 하나와, 그 이미지를 다룰 권한까지 받은 사람.

    커스터마이즈되지 않은 이미지에는 주인이 없다. 게이트를 열어도 소유권 검사가 남는 것을
    보는 자리이므로, 권한은 주되 주인은 아닌 상태를 세운다.
    """

    granted: bool = True

    @override
    def describe(self) -> str:
        holds = "그 이미지에 권한 있음" if self.granted else "아무 권한도 없음"
        return f"주인 없는 이미지 하나, {holds}인 사용자 한 명"

    @override
    async def lay(self, seeding: Any) -> AnImageAndACaller:
        domain = await seeding.creating(SeedDomain(name_hint="home"))
        registry = await seeding.creating(SeedContainerRegistry(name_hint="host"))
        image = await seeding.creating_from(SeedImage(), registry)
        caller = await seeding.within(SomeoneOf(domain))
        if self.granted:
            await seeding.within(SomeoneReachingImages(registry, caller))
        return AnImageAndACaller(seeding.made(image), seeding.made(caller))


@dataclass(frozen=True)
class AnImageTheCallerMade(Given[Any, AnImageAndACaller]):
    """부르는 사람이 만든 커스텀 이미지 하나와, 그 이미지를 다룰 권한.

    소유권 검사를 통과하는 유일한 모양이다. 커스터마이즈된 것이면서 만든 사람이 부르는
    사람이어야 한다.
    """

    status: ImageStatus = ImageStatus.ALIVE

    @override
    def describe(self) -> str:
        marked = "" if self.status is ImageStatus.ALIVE else f", 상태는 {self.status.value}"
        return f"부르는 사람이 만든 커스텀 이미지 하나{marked}, 그 이미지에 권한 있음"

    @override
    async def lay(self, seeding: Any) -> AnImageAndACaller:
        domain = await seeding.creating(SeedDomain(name_hint="home"))
        registry = await seeding.creating(SeedContainerRegistry(name_hint="host"))
        caller = await seeding.within(SomeoneOf(domain))
        made = seeding.made(caller)
        image = await seeding.creating_from(
            SeedImage(customized=True, creator_id=UserID(made.id), status=self.status),
            registry,
        )
        await seeding.within(SomeoneReachingImages(registry, caller))
        return AnImageAndACaller(seeding.made(image), made)


@dataclass(frozen=True)
class ManyImagesAndSomeone(Given[Any, ManyImagesAndACaller]):
    """한 레지스트리 안의 이미지 여럿과, 부를 사람 하나."""

    role: UserRole = UserRole.SUPERADMIN
    count: int = 2

    @override
    def describe(self) -> str:
        return f"레지스트리 하나와 그 안의 이미지 {self.count}개, {self.role.value} 한 명"

    @override
    async def lay(self, seeding: Any) -> ManyImagesAndACaller:
        domain = await seeding.creating(SeedDomain(name_hint="home"))
        registry = await seeding.creating(SeedContainerRegistry(name_hint="host"))
        images = [
            await seeding.creating_from(SeedImage(name_hint=f"image-{index}"), registry)
            for index in range(self.count)
        ]
        caller = await seeding.within(SomeoneOf(domain, role=self.role))
        return ManyImagesAndACaller(
            laid=tuple(seeding.made(one) for one in images),
            named=seeding.made(images[0]),
            registry=seeding.made(registry),
            caller=seeding.made(caller),
        )


@dataclass(frozen=True)
class AnAliasAndSomeone(Given[Any, AnAliasAndACaller]):
    """별칭이 붙은 이미지 하나와, 부를 사람 하나."""

    role: UserRole = UserRole.SUPERADMIN

    @override
    def describe(self) -> str:
        return f"별칭이 붙은 이미지 하나, {self.role.value} 한 명"

    @override
    async def lay(self, seeding: Any) -> AnAliasAndACaller:
        domain = await seeding.creating(SeedDomain(name_hint="home"))
        registry = await seeding.creating(SeedContainerRegistry(name_hint="host"))
        image = await seeding.creating_from(SeedImage(), registry)
        alias = await seeding.adding(SeedAlias(), image)
        caller = await seeding.within(SomeoneOf(domain, role=self.role))
        return AnAliasAndACaller(
            image=seeding.made(image),
            alias=seeding.made(alias),
            caller=seeding.made(caller),
        )


@dataclass(frozen=True)
class SomeoneReachingImages(SeedNest[Laid[None]]):
    """그 레지스트리 안의 이미지를 읽고 잊고 지울 수 있는 사용자.

    이미지는 자기를 담은 레지스트리 아래에 만들어진다. 그래서 역할이 앉는 스코프는 이미지가
    아니라 레지스트리다.
    """

    registry: Laid[ContainerRegistryData]
    someone: Laid[UserData]

    @override
    def kind(self) -> str:
        return "이미지를 다룰 권한을 받은 사용자 준비"

    @override
    def lay(self, seed: Seeder) -> Laid[None]:
        role = seed.creating_from(
            SeedRole(lambda one: ContainerRegistryID(one.id), name_hint="image-keeper"),
            self.registry,
        )
        for allowed in REACHING:
            seed.adding(SeedPermission(entity_type=ImageEntityType(), permission=allowed), role)
        return seed.granting(
            role, self.someone, role_id=lambda r: r.id, user_id=lambda u: UserID(u.id)
        )


@dataclass(frozen=True)
class TheImageNode(Then[AnImageAndACaller, ImageNode]):
    """심은 이미지가 통째로 온다. 시나리오가 바꾼 자리만 여기로 받는다."""

    status: ImageStatus | None = None

    @override
    def says(self) -> str:
        return "심은 이미지 전체가 온다"

    @override
    def look(self, laid: AnImageAndACaller, answered: Answered[ImageNode]) -> list[Verdict]:
        node = answered.response
        if node is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        return [
            Same("name", node.name, laid.image.name),
            Same("registry", node.registry, laid.image.registry),
            Same("architecture", node.architecture, laid.image.architecture),
            Same("tag", node.tag, laid.image.tag),
            Same("status", node.status, self.status or laid.image.status),
            Same("is_local", node.is_local, laid.image.is_local),
            Same("size_bytes", node.size_bytes, laid.image.size_bytes),
            Skipped("id", "데이터베이스가 만든다"),
            Skipped("last_used_at", "세션이 쓰는 값이라 이 실행이 말할 수 없다"),
        ]


class Target(ABC):
    """요청이 지목하는 이미지."""

    @abstractmethod
    def says(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def id_of(self, laid: AnImageAndACaller) -> uuid.UUID:
        raise NotImplementedError


@dataclass(frozen=True)
class TheLaidImage(Target):
    """전제가 심어 둔 그 이미지."""

    @override
    def says(self) -> str:
        return "심은 이미지"

    @override
    def id_of(self, laid: AnImageAndACaller) -> uuid.UUID:
        return laid.image.id


@dataclass(frozen=True)
class AnIdThatHoldsNothing(Target):
    """아무 이미지도 갖지 않는 id."""

    @override
    def says(self) -> str:
        return "아무것도 갖지 않은 id"

    @override
    def id_of(self, laid: AnImageAndACaller) -> uuid.UUID:
        return NOTHING


class Paging(ABC):
    """검색 요청이 한 쪽을 고르는 방식."""

    @abstractmethod
    def says(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def asked(self) -> dict[str, Any]:
        raise NotImplementedError


@dataclass(frozen=True)
class ByOffset(Paging):
    """크기와 건너뛸 수로 고른다. 생략하면 어댑터가 기본 크기를 채운다."""

    limit: int | None = None

    @override
    def says(self) -> str:
        return "크기를 생략하고" if self.limit is None else "조건 없이"

    @override
    def asked(self) -> dict[str, Any]:
        return {"limit": self.limit}


@dataclass(frozen=True)
class ByCursor(Paging):
    """커서로 앞에서부터 고른다."""

    first: int

    @override
    def says(self) -> str:
        return "커서로 앞에서부터"

    @override
    def asked(self) -> dict[str, Any]:
        return {"first": self.first}


@dataclass(frozen=True)
class ByABrokenCursor(Paging):
    """읽을 수 없는 커서 값을 준다."""

    @override
    def says(self) -> str:
        return "깨진 커서로"

    @override
    def asked(self) -> dict[str, Any]:
        return {"first": 1, "after": "not-a-cursor"}


@dataclass(frozen=True)
class ByTwoModesAtOnce(Paging):
    """크기와 커서를 함께 준다. 어댑터가 방식을 고를 수 없는 자리다."""

    @override
    def says(self) -> str:
        return "크기와 커서를 함께 주고"

    @override
    def asked(self) -> dict[str, Any]:
        return {"first": 1, "limit": 1}
