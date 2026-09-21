"""What an image scenario table says besides the call.

How the adapter is built lives in the tables' own conftest, and the rows a scenario
lays come from ``seeds``. This holds what is left: the types these tables are written
against, and the situations worth naming more than once.
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, override

from ai.backend.common.data.entity.container_registry import ContainerRegistryID
from ai.backend.common.data.entity.image import ImageEntityType
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.image.response import ImageNode
from ai.backend.common.dto.manager.v2.image.types import (
    ImageLabelInfo,
    ImageResourceLimitGQLInfo,
    ImageResourceLimitInfo,
)
from ai.backend.manager.data.container_registry.types import ContainerRegistryData
from ai.backend.manager.data.image.types import ImageAliasData, ImageData, ImageStatus, ImageType
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.defs import INTRINSIC_SLOTS_MIN
from ai.backend.testutils.scenario_steps import (
    Answered,
    Condition,
    Given,
    Held,
    Same,
    SameAs,
    Skipped,
    Then,
    Verdict,
)
from bai_scenario.components.domain import SomeoneOf, WrittenByThisRun
from bai_scenario.seeds.domain.domain import SeedDomain
from bai_scenario.seeds.image.image import SeedAlias, SeedImage
from bai_scenario.seeds.image.registry import SeedContainerRegistry
from bai_scenario.seeds.rbac.role import SeedPermission, SeedRole
from bai_scenario.seeds.seeder import Laid, Seeder, SeedNest

NOTHING = uuid.UUID("00000000-0000-0000-0000-0000000000ff")
"""어느 행도 가리키지 않는 ID. 대상이 없을 때 무엇이 반환되는지 확인하려고 지정한다."""

DEFAULT_LIMITS = [
    ImageResourceLimitInfo(key=str(slot), min=str(least), max=None)
    for slot, least in sorted(INTRINSIC_SLOTS_MIN.items())
]
"""라벨로 하한을 지정하지 않은 이미지에 채워지는 기본 하한. 값은 src가 정한 상수에서 읽는다."""

DEFAULT_LIMITS_GQL = [
    ImageResourceLimitGQLInfo(key=str(slot), min=str(least), max="Infinity")
    for slot, least in sorted(INTRINSIC_SLOTS_MIN.items())
]
"""같은 하한의 GQL 표현. 상한이 없는 필드에는 Infinity가 들어간다."""


class Accelerators(ABC):
    """이미지에 지정된 가속기."""

    @abstractmethod
    def named(self) -> str | None:
        """이미지 행에 저장되는 값."""
        raise NotImplementedError

    @abstractmethod
    def supported(self) -> list[str]:
        """노드가 그 값을 펼쳐 반환하는 목록."""
        raise NotImplementedError


@dataclass(frozen=True)
class NoAccelerator(Accelerators):
    """가속기를 지정하지 않은 상태. 무엇이든 허용한다는 의미로 펼쳐진다."""

    @override
    def named(self) -> str | None:
        return None

    @override
    def supported(self) -> list[str]:
        return ["*"]


@dataclass(frozen=True)
class OneAccelerator(Accelerators):
    """가속기 하나를 지정한 상태."""

    name: str = "cuda"

    @override
    def named(self) -> str | None:
        return self.name

    @override
    def supported(self) -> list[str]:
        return [self.name]


REACHING = (Permission.READ, Permission.SOFT_DELETE, Permission.HARD_DELETE)
"""이미지를 조회하고 소프트 삭제하고 완전 삭제하는 데 필요한 권한.

권한 행 하나가 비트 하나만 담으므로 3개를 따로 만든다. 역할은 하나다."""


@dataclass(frozen=True)
class AnImageAndACaller:
    """이미지 1개와 호출자."""

    image: ImageData
    caller: UserData


@dataclass(frozen=True)
class ManyImagesAndACaller:
    """이미지 여러 개와 호출자. `named`는 그중 지정해서 쓸 하나다."""

    laid: tuple[ImageData, ...]
    named: ImageData
    registry: ContainerRegistryData
    caller: UserData


@dataclass(frozen=True)
class AnAliasAndACaller:
    """별칭이 등록된 이미지 1개와 호출자."""

    image: ImageData
    alias: ImageAliasData
    caller: UserData


@dataclass(frozen=True)
class AliasesAndACaller:
    """이미지 2개에 나뉘어 등록된 별칭과 호출자."""

    image: ImageData
    aliases: tuple[ImageAliasData, ...]
    caller: UserData


@dataclass(frozen=True)
class ARegistryWithImages(SeedNest[tuple[ContainerRegistryData, tuple[Laid[ImageData], ...]]]):
    """레지스트리 1개와 그 안의 이미지들. 이미지는 레지스트리에 속해야 만들 수 있다."""

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
    """이미지 1개와 호출자 1명."""

    role: UserRole = UserRole.USER
    status: ImageStatus = ImageStatus.ALIVE
    accelerators: Accelerators = field(default_factory=NoAccelerator)

    @override
    def describe(self) -> str:
        marked = "" if self.status is ImageStatus.ALIVE else f", 상태는 {self.status.value}"
        return f"레지스트리 1개와 그 안의 이미지 1개{marked}, {self.role.value} 1명"

    @override
    async def lay(self, seeding: Any) -> AnImageAndACaller:
        domain = await seeding.creating(SeedDomain(name_hint="home"))
        registry = await seeding.creating(SeedContainerRegistry(name_hint="host"))
        image = await seeding.creating_from(
            SeedImage(status=self.status, accelerators=self.accelerators.named()), registry
        )
        caller = await seeding.within(SomeoneOf(domain, role=self.role))
        return AnImageAndACaller(seeding.made(image), seeding.made(caller))


@dataclass(frozen=True)
class AnUncustomizedImageAndSomeone(Given[Any, AnImageAndACaller]):
    """커스텀 이미지가 아닌 이미지와 일반 사용자."""

    granted: bool = True

    @override
    def describe(self) -> str:
        holds = "그 이미지에 권한 있음" if self.granted else "아무 권한도 없음"
        return f"커스텀 이미지가 아닌 이미지 1개, {holds}인 사용자 1명"

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
    """호출자가 만든 커스텀 이미지 1개와, 그 이미지에 대한 권한.

    커스텀 이미지 작성자 검사를 통과하려면 두 조건이 모두 필요하다.
    """

    status: ImageStatus = ImageStatus.ALIVE

    @override
    def describe(self) -> str:
        marked = "" if self.status is ImageStatus.ALIVE else f", 상태는 {self.status.value}"
        return f"호출자가 만든 커스텀 이미지 1개{marked}, 그 이미지에 권한 있음"

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
    """레지스트리 1개 안의 이미지 여러 개와 호출자 1명."""

    role: UserRole = UserRole.SUPERADMIN
    count: int = 2

    @override
    def describe(self) -> str:
        return f"레지스트리 1개와 그 안의 이미지 {self.count}개, {self.role.value} 1명"

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
class ImagesWithTwoStatuses(Given[Any, ManyImagesAndACaller]):
    """살아 있는 이미지와 삭제된 이미지, 슈퍼관리자."""

    @override
    def describe(self) -> str:
        return "살아 있는 이미지 1개와 삭제된 이미지 1개, superadmin 1명"

    @override
    async def lay(self, seeding: Any) -> ManyImagesAndACaller:
        domain = await seeding.creating(SeedDomain(name_hint="home"))
        registry = await seeding.creating(SeedContainerRegistry(name_hint="host"))
        alive = await seeding.creating_from(
            SeedImage(name_hint="alive", status=ImageStatus.ALIVE), registry
        )
        await seeding.creating_from(
            SeedImage(name_hint="deleted", status=ImageStatus.DELETED), registry
        )
        caller = await seeding.within(SomeoneOf(domain, role=UserRole.SUPERADMIN))
        made_alive = seeding.made(alive)
        return ManyImagesAndACaller(
            laid=(made_alive,),
            named=made_alive,
            registry=seeding.made(registry),
            caller=seeding.made(caller),
        )


@dataclass(frozen=True)
class ImagesInTwoRegistries(Given[Any, ManyImagesAndACaller]):
    """레지스트리 2개에 나뉘어 있는 이미지들과 호출자 1명.

    한쪽으로 좁히는 동작을 확인할 때 쓴다. 레지스트리가 1개뿐이면 좁혀도 걸러지는 것이
    없어서, 조건을 빼도 같은 응답이 반환된다.
    """

    role: UserRole = UserRole.SUPERADMIN
    wanted: int = 2
    elsewhere: int = 2

    @override
    def describe(self) -> str:
        return (
            f"레지스트리 2개, 한쪽에 이미지 {self.wanted}개와 다른 쪽에 {self.elsewhere}개, "
            f"{self.role.value} 1명"
        )

    @override
    async def lay(self, seeding: Any) -> ManyImagesAndACaller:
        domain = await seeding.creating(SeedDomain(name_hint="home"))
        wanted = await seeding.creating(SeedContainerRegistry(name_hint="wanted"))
        other = await seeding.creating(SeedContainerRegistry(name_hint="other"))
        here = [
            await seeding.creating_from(SeedImage(name_hint=f"here-{index}"), wanted)
            for index in range(self.wanted)
        ]
        for index in range(self.elsewhere):
            await seeding.creating_from(SeedImage(name_hint=f"there-{index}"), other)
        caller = await seeding.within(SomeoneOf(domain, role=self.role))
        return ManyImagesAndACaller(
            laid=tuple(seeding.made(one) for one in here),
            named=seeding.made(here[0]),
            registry=seeding.made(wanted),
            caller=seeding.made(caller),
        )


@dataclass(frozen=True)
class AnAliasAndSomeone(Given[Any, AnAliasAndACaller]):
    """별칭이 등록된 이미지 1개와 호출자 1명."""

    role: UserRole = UserRole.SUPERADMIN

    @override
    def describe(self) -> str:
        return f"별칭이 등록된 이미지 1개, {self.role.value} 1명"

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
class AnAliasAndAPlainUser(Given[Any, AnAliasAndACaller]):
    """별칭이 등록된 이미지 1개와, 그 이미지에 권한을 받았거나 받지 않은 일반 사용자."""

    granted: bool = True

    @override
    def describe(self) -> str:
        holds = "그 이미지에 권한 있음" if self.granted else "아무 권한도 없음"
        return f"별칭이 등록된 이미지 1개, {holds}인 사용자 1명"

    @override
    async def lay(self, seeding: Any) -> AnAliasAndACaller:
        domain = await seeding.creating(SeedDomain(name_hint="home"))
        registry = await seeding.creating(SeedContainerRegistry(name_hint="host"))
        image = await seeding.creating_from(SeedImage(), registry)
        alias = await seeding.adding(SeedAlias(), image)
        caller = await seeding.within(SomeoneOf(domain))
        if self.granted:
            await seeding.within(SomeoneReachingImages(registry, caller))
        return AnAliasAndACaller(
            image=seeding.made(image),
            alias=seeding.made(alias),
            caller=seeding.made(caller),
        )


@dataclass(frozen=True)
class AliasesOnTwoImagesAndSomeone(Given[Any, AliasesAndACaller]):
    """이미지 2개에 별칭 3개가 나뉘어 등록된 상태와 슈퍼관리자."""

    @override
    def describe(self) -> str:
        return "이미지 2개, 한쪽에 별칭 2개와 다른 쪽에 1개, superadmin 1명"

    @override
    async def lay(self, seeding: Any) -> AliasesAndACaller:
        domain = await seeding.creating(SeedDomain(name_hint="home"))
        registry = await seeding.creating(SeedContainerRegistry(name_hint="host"))
        wanted = await seeding.creating_from(SeedImage(name_hint="wanted"), registry)
        other = await seeding.creating_from(SeedImage(name_hint="other"), registry)
        first = await seeding.adding(SeedAlias(alias="alpha"), wanted)
        second = await seeding.adding(SeedAlias(alias="zeta"), wanted)
        await seeding.adding(SeedAlias(alias="middle"), other)
        caller = await seeding.within(SomeoneOf(domain, role=UserRole.SUPERADMIN))
        return AliasesAndACaller(
            image=seeding.made(wanted),
            aliases=(seeding.made(first), seeding.made(second)),
            caller=seeding.made(caller),
        )


@dataclass(frozen=True)
class SomeoneReachingImages(SeedNest[Laid[None]]):
    """그 레지스트리 안의 이미지를 조회·소프트 삭제·완전 삭제할 수 있는 사용자.

    이미지는 자신을 담은 레지스트리 아래에 만들어진다. 그래서 역할이 놓이는 스코프는
    이미지가 아니라 레지스트리다.
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
class Filled(Condition[Any]):
    """값이 채워져 반환된다. 비어 있으면 그 안의 필드를 확인할 수 없다."""

    @override
    def says(self) -> str:
        return "값이 채워져 반환된다"

    @override
    def holds(self, got: Any) -> bool:
        return got is not None


@dataclass(frozen=True)
class TheImageNode(Then[Any, ImageNode]):
    """이미지 노드의 전체 필드를 확인한다. 시나리오가 바꾼 필드만 인자로 받는다.

    이미지를 담은 전제면 무엇이든 받는다. `image` 필드로 이미지 1개를 들고 있으면 된다.
    """

    name: str | None = None
    registry: str | None = None
    image: str | None = None
    status: ImageStatus | None = None
    tag: str | None = None
    architecture: str | None = None
    size_bytes: int | None = None
    image_type: ImageType | None = None
    config_digest: str | None = None
    is_local: bool | None = None
    labels: dict[str, str] | None = None
    resource_limits: list[ImageResourceLimitInfo] | None = None
    resource_limits_gql: list[ImageResourceLimitGQLInfo] | None = None
    accelerators: Accelerators = field(default_factory=NoAccelerator)

    @override
    def says(self) -> str:
        return "이미지 노드의 모든 필드가 예상값과 일치한다"

    @override
    def look(self, laid: Any, answered: Answered[ImageNode]) -> list[Verdict]:
        node = answered.response
        if node is None:
            return [Held("응답", node, Filled())]
        identity, metadata, requirements = node.identity, node.metadata, node.requirements
        if identity is None or metadata is None or requirements is None:
            return [
                Held("identity", identity, Filled()),
                Held("metadata", metadata, Filled()),
                Held("requirements", requirements, Filled()),
            ]
        image: ImageData = laid.image
        planted: uuid.UUID = image.id
        name = self.name if self.name is not None else str(image.name)
        registry = self.registry if self.registry is not None else image.registry
        namespace = self.image if self.image is not None else image.image
        status = self.status if self.status is not None else image.status
        tag = self.tag if self.tag is not None else image.tag
        architecture = self.architecture if self.architecture is not None else image.architecture
        size_bytes = self.size_bytes if self.size_bytes is not None else image.size_bytes
        image_type = self.image_type if self.image_type is not None else image.type
        config_digest = (
            self.config_digest if self.config_digest is not None else image.config_digest
        )
        is_local = self.is_local if self.is_local is not None else image.is_local
        labels = self.labels if self.labels is not None else image.labels.label_data
        label_nodes = sorted(
            (ImageLabelInfo(key=key, value=value) for key, value in labels.items()),
            key=lambda one: one.key,
        )
        resource_limits = (
            self.resource_limits if self.resource_limits is not None else DEFAULT_LIMITS
        )
        resource_limits_gql = (
            self.resource_limits_gql if self.resource_limits_gql is not None else DEFAULT_LIMITS_GQL
        )
        written = WrittenByThisRun(datetime.now(UTC))
        return [
            Held("id", node.id, SameAs(planted, "미리 만들어 둔 이미지의 ID")),
            Same("name", node.name, name),
            Same("image", node.image, namespace),
            Same("registry", node.registry, registry),
            Held(
                "registry_id",
                node.registry_id,
                SameAs(image.registry_id, "미리 만들어 둔 레지스트리의 ID"),
            ),
            Same("project", node.project, image.project),
            Same("tag", node.tag, tag),
            Same("architecture", node.architecture, architecture),
            Same("size_bytes", node.size_bytes, size_bytes),
            Same("type", node.type, image_type),
            Same("status", node.status, status),
            Same("labels", sorted(node.labels, key=lambda one: one.key), label_nodes),
            Same("tags", node.tags, []),
            Same(
                "resource_limits",
                sorted(node.resource_limits, key=lambda one: one.key),
                resource_limits,
            ),
            Same("accelerators", node.accelerators, self.accelerators.named()),
            Same("config_digest", node.config_digest, config_digest),
            Same("is_local", node.is_local, is_local),
            Held("created_at", node.created_at, written),
            Skipped("last_used_at", "세션이 기록하는 값이라 이 실행에서는 알 수 없다"),
            Same("identity.canonical_name", identity.canonical_name, name),
            Same("identity.namespace", identity.namespace, namespace),
            Same("identity.architecture", identity.architecture, architecture),
            Same("metadata.digest", metadata.digest, config_digest),
            Same("metadata.size_bytes", metadata.size_bytes, size_bytes),
            Held("metadata.created_at", metadata.created_at, written),
            Held(
                "metadata.last_used_at",
                metadata.last_used_at,
                SameAs(node.last_used_at, "노드의 last_used_at 필드"),
            ),
            Same("metadata.tags", metadata.tags, []),
            Same(
                "metadata.labels",
                sorted(metadata.labels, key=lambda one: one.key),
                label_nodes,
            ),
            Same("metadata.status", metadata.status, status),
            Same(
                "requirements.supported_accelerators",
                requirements.supported_accelerators,
                self.accelerators.supported(),
            ),
            Same(
                "requirements.resource_limits",
                sorted(requirements.resource_limits, key=lambda one: one.key),
                resource_limits_gql,
            ),
        ]


class Target(ABC):
    """요청이 지정하는 이미지."""

    @abstractmethod
    def says(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def id_of(self, laid: AnImageAndACaller) -> uuid.UUID:
        raise NotImplementedError


@dataclass(frozen=True)
class TheLaidImage(Target):
    """전제에서 미리 만들어 둔 이미지."""

    @override
    def says(self) -> str:
        return "미리 만들어 둔 이미지"

    @override
    def id_of(self, laid: AnImageAndACaller) -> uuid.UUID:
        return laid.image.id


@dataclass(frozen=True)
class AnIdThatHoldsNothing(Target):
    """어느 이미지도 가리키지 않는 ID."""

    @override
    def says(self) -> str:
        return "어느 이미지도 가리키지 않는 ID"

    @override
    def id_of(self, laid: AnImageAndACaller) -> uuid.UUID:
        return NOTHING


class Paging(ABC):
    """검색 요청이 페이지를 고르는 방식."""

    @abstractmethod
    def says(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def asked(self) -> dict[str, Any]:
        raise NotImplementedError


@dataclass(frozen=True)
class ByOffset(Paging):
    """크기와 오프셋으로 고른다. 생략하면 어댑터가 기본 크기를 채운다."""

    limit: int | None = None
    offset: int | None = None

    @override
    def says(self) -> str:
        if self.limit is None:
            return "페이지 크기를 생략하고"
        if self.offset is not None:
            return f"앞의 {self.offset}개를 건너뛰고 한 페이지에 {self.limit}개씩"
        return f"한 페이지에 {self.limit}개씩"

    @override
    def asked(self) -> dict[str, Any]:
        return {"limit": self.limit, "offset": self.offset}


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
    """해석할 수 없는 커서 값을 지정한다."""

    @override
    def says(self) -> str:
        return "잘못된 커서로"

    @override
    def asked(self) -> dict[str, Any]:
        return {"first": 1, "after": "not-a-cursor"}


@dataclass(frozen=True)
class ByTwoModesAtOnce(Paging):
    """크기와 커서를 함께 지정한다. 어댑터가 페이지 방식을 고를 수 없는 경우다."""

    @override
    def says(self) -> str:
        return "크기와 커서를 함께 지정하고"

    @override
    def asked(self) -> dict[str, Any]:
        return {"first": 1, "limit": 1}
