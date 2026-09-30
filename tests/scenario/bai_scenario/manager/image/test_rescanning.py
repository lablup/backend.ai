"""태그 하나 스캔 — 레지스트리에서 태그를 읽어 요청한 아키텍처의 이미지 하나를 돌려준다."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, override
from uuid import UUID

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.image.request import RescanImagesInput
from ai.backend.common.dto.manager.v2.image.response import ImageNode
from ai.backend.manager.api.adapters.image.adapter import ImageAdapter
from ai.backend.manager.data.container_registry.types import ContainerRegistryData
from ai.backend.manager.data.image.types import ImageStatus, ImageType
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.errors.image import ImageNotFound, RegistryNotFoundForImage
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    Same,
    SameAs,
    Scenario,
    Skipped,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.domain import SomeoneOf, WrittenByThisRun
from bai_scenario.components.image import DEFAULT_LIMITS, DEFAULT_LIMITS_GQL, Filled
from bai_scenario.fakes.container_registry import CONFIG_SIZE, ServedTag, serving
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario
from bai_scenario.seeds.domain.domain import SeedDomain
from bai_scenario.seeds.image.registry import SeedContainerRegistry

PROJECT = "stable"
SERVED = ServedTag(repository=f"{PROJECT}/python", tag="latest", architectures=("amd64", "arm64"))
MISSING_TAG = "removed"
ANY_ACCELERATOR = "*"
"""가속기 레이블이 없는 이미지에 스캐너가 적는 값. 모든 가속기에서 돈다는 뜻이다."""


@dataclass(frozen=True)
class ARegistryAndACaller:
    """태그를 내놓는 레지스트리 1개와 호출자."""

    registry: ContainerRegistryData
    caller: UserData


@dataclass(frozen=True)
class ARegistryServingATag(Given[Any, ARegistryAndACaller]):
    """레지스트리 1개와 호출자 1명. 레지스트리는 태그 하나를 두 아키텍처로 내놓는다."""

    role: UserRole = UserRole.SUPERADMIN

    @override
    def describe(self) -> str:
        arches = ", ".join(SERVED.architectures)
        return (
            f"{SERVED.repository}:{SERVED.tag} 태그를 {arches}로 내놓는 레지스트리 1개, "
            f"{self.role.value} 1명"
        )

    @override
    async def lay(self, seeding: Any) -> ARegistryAndACaller:
        domain = await seeding.creating(SeedDomain(name_hint="home"))
        registry = await seeding.creating(SeedContainerRegistry(name_hint="host", project=PROJECT))
        caller = await seeding.within(SomeoneOf(domain, role=self.role))
        return ARegistryAndACaller(seeding.made(registry), seeding.made(caller))


class Canonical:
    """스캔을 요청하는 이름."""

    def __init__(self, tag: str | None) -> None:
        self._tag = tag

    def of(self, registry: ContainerRegistryData) -> str:
        if self._tag is None:
            return f"{registry.registry_name}/{registry.project}"
        return f"{registry.registry_name}/{SERVED.repository}:{self._tag}"

    def says(self) -> str:
        if self._tag is None:
            return "이미지 없이 레지스트리 이름만"
        return f"{SERVED.repository}:{self._tag} 태그를"


THE_SERVED_TAG = Canonical(SERVED.tag)
A_MISSING_TAG = Canonical(MISSING_TAG)
THE_REGISTRY_ALONE = Canonical(None)


@dataclass(frozen=True)
class Rescanning(When[ARegistryAndACaller, ImageAdapter, ImageNode]):
    """태그 하나를 아키텍처를 지정해 스캔한다."""

    canonical: Canonical = THE_SERVED_TAG
    architecture: str = "x86_64"

    @override
    def operation(self) -> str:
        return "admin_rescan_image"

    @override
    def describe(self, laid: ARegistryAndACaller) -> str:
        return (
            f"{laid.caller.username}이 {self.canonical.says()} {self.architecture} 아키텍처로 스캔"
        )

    @override
    async def call(self, adapter: ImageAdapter, laid: ARegistryAndACaller) -> ImageNode:
        asked = RescanImagesInput(
            canonical=self.canonical.of(laid.registry), architecture=self.architecture
        )
        with serving(laid.registry, SERVED), ActingAs(laid.caller):
            payload = await adapter.admin_rescan_image(asked)
        return payload.item


@dataclass(frozen=True)
class TheScannedImageNode(Then[ARegistryAndACaller, ImageNode]):
    """레지스트리가 내놓은 태그로 새로 등록된 이미지 노드의 전체 필드를 확인한다."""

    @override
    def says(self) -> str:
        return "요청한 아키텍처로 등록된 이미지 노드가 반환된다"

    @override
    def look(self, laid: ARegistryAndACaller, answered: Answered[ImageNode]) -> list[Verdict]:
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
        registry = laid.registry
        name = f"{registry.registry_name}/{SERVED.repository}:{SERVED.tag}"
        written = WrittenByThisRun(datetime.now(UTC))
        return [
            Skipped("id", "스캔이 새로 만든 행이라 데이터베이스가 정한다"),
            Same("name", node.name, name),
            Same("image", node.image, SERVED.repository),
            Same("registry", node.registry, registry.registry_name),
            Held(
                "registry_id",
                node.registry_id,
                SameAs[UUID](registry.id, "미리 만들어 둔 레지스트리의 ID"),
            ),
            Same("project", node.project, PROJECT),
            Same("tag", node.tag, SERVED.tag),
            Same("architecture", node.architecture, "x86_64"),
            Same("size_bytes", node.size_bytes, CONFIG_SIZE),
            Same("type", node.type, ImageType.COMPUTE),
            Same("status", node.status, ImageStatus.ALIVE),
            Same("labels", node.labels, []),
            Same("tags", node.tags, []),
            Same(
                "resource_limits",
                sorted(node.resource_limits, key=lambda one: one.key),
                DEFAULT_LIMITS,
            ),
            Same("accelerators", node.accelerators, ANY_ACCELERATOR),
            Same("config_digest", node.config_digest, "sha256:config-amd64"),
            Same("is_local", node.is_local, False),
            Held("created_at", node.created_at, written),
            Skipped("last_used_at", "세션이 기록하는 값이라 이 실행에서는 알 수 없다"),
            Same("identity.canonical_name", identity.canonical_name, name),
            Same("identity.namespace", identity.namespace, SERVED.repository),
            Same("identity.architecture", identity.architecture, "x86_64"),
            Same("metadata.digest", metadata.digest, "sha256:config-amd64"),
            Same("metadata.size_bytes", metadata.size_bytes, CONFIG_SIZE),
            Held("metadata.created_at", metadata.created_at, written),
            Held(
                "metadata.last_used_at",
                metadata.last_used_at,
                SameAs(node.last_used_at, "노드의 last_used_at 필드"),
            ),
            Same("metadata.tags", metadata.tags, []),
            Same("metadata.labels", metadata.labels, []),
            Same("metadata.status", metadata.status, ImageStatus.ALIVE),
            Same(
                "requirements.supported_accelerators",
                requirements.supported_accelerators,
                [ANY_ACCELERATOR],
            ),
            Same(
                "requirements.resource_limits",
                sorted(requirements.resource_limits, key=lambda one: one.key),
                DEFAULT_LIMITS_GQL,
            ),
        ]


@dataclass(frozen=True)
class ScanningAnUnregisteredImage(
    Scenario[SeedingSession, ARegistryAndACaller, ImageAdapter, ImageNode]
):
    @override
    def summary(self) -> str:
        return "scanning-an-unregistered-image-registers-the-requested-architecture"

    @override
    def describe(self) -> str:
        return (
            "슈퍼관리자가 미등록된 이미지를 scan하면 요청한 아키텍처의 이미지 하나가 반환된다. "
            "scan은 슈퍼관리자 역할이 있어야만 실행된다"
        )

    @override
    def given(self) -> Given[SeedingSession, ARegistryAndACaller]:
        return ARegistryServingATag()

    @override
    def when(self) -> When[ARegistryAndACaller, ImageAdapter, ImageNode]:
        return Rescanning()

    @override
    def then(self) -> Then[ARegistryAndACaller, ImageNode]:
        return TheScannedImageNode()


@dataclass(frozen=True)
class APlainUserMayNotScan(Scenario[SeedingSession, ARegistryAndACaller, ImageAdapter, ImageNode]):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-may-not-scan"

    @override
    def describe(self) -> str:
        return "일반 사용자는 scan을 실행할 수 없어 슈퍼관리자 권한 부족으로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, ARegistryAndACaller]:
        return ARegistryServingATag(role=UserRole.USER)

    @override
    def when(self) -> When[ARegistryAndACaller, ImageAdapter, ImageNode]:
        return Rescanning()

    @override
    def then(self) -> Then[ARegistryAndACaller, ImageNode]:
        return TheCallIsRefused(InsufficientPrivilege)


@dataclass(frozen=True)
class NoRegistryMatchesTheImage(
    Scenario[SeedingSession, ARegistryAndACaller, ImageAdapter, ImageNode]
):
    @override
    def summary(self) -> str:
        return "a-name-no-registry-holds-as-an-image-is-refused-without-a-scan"

    @override
    def describe(self) -> str:
        return (
            "이미지에 맞는 registry가 없으면 scan하지 않고 거부한다. "
            "레지스트리 이름만 주어도 레지스트리 전체를 스캔하지 않는다"
        )

    @override
    def given(self) -> Given[SeedingSession, ARegistryAndACaller]:
        return ARegistryServingATag()

    @override
    def when(self) -> When[ARegistryAndACaller, ImageAdapter, ImageNode]:
        return Rescanning(canonical=THE_REGISTRY_ALONE)

    @override
    def then(self) -> Then[ARegistryAndACaller, ImageNode]:
        return TheCallIsRefused(RegistryNotFoundForImage)


@dataclass(frozen=True)
class AMissingTagIsNotASuccess(
    Scenario[SeedingSession, ARegistryAndACaller, ImageAdapter, ImageNode]
):
    @override
    def summary(self) -> str:
        return "a-tag-the-registry-does-not-hold-is-refused"

    @override
    def describe(self) -> str:
        return "레지스트리에 없는 태그를 scan하면 이미지를 찾을 수 없어 거부된다"

    @override
    def given(self) -> Given[SeedingSession, ARegistryAndACaller]:
        return ARegistryServingATag()

    @override
    def when(self) -> When[ARegistryAndACaller, ImageAdapter, ImageNode]:
        return Rescanning(canonical=A_MISSING_TAG)

    @override
    def then(self) -> Then[ARegistryAndACaller, ImageNode]:
        return TheCallIsRefused(ImageNotFound)


SCENARIOS: list[Any] = [
    ScanningAnUnregisteredImage(),
    APlainUserMayNotScan(),
    NoRegistryMatchesTheImage(),
    AMissingTagIsNotASuccess(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_rescanning(
    scenario: Any, adapter: ImageAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
