"""레지스트리 하나를 id 로, 이름으로, 그리고 아무 키 없이 읽기."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override
from uuid import UUID

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.artifact_registry.response import ArtifactRegistryGQLNode
from ai.backend.common.exception import InvalidAPIParameters
from ai.backend.manager.api.adapters.artifact_registry.adapter import ArtifactRegistryAdapter
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.errors.artifact_registry import ArtifactRegistryNotFoundError
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Says, Scenario, Then, When
from bai_scenario.components.artifact_registry import (
    ARegistryAndACaller,
    ARegistryAndSomeone,
    TheRegistryNode,
)
from bai_scenario.components.domain import TheCallIsRefused
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

MISSING = UUID(int=1)
"""어떤 행도 가리키는 레지스트리가 없는 id."""

UNKNOWN_NAME = "no-such-registry"

type RegistryStep = Scenario[
    TestSeedingSession, ARegistryAndACaller, ArtifactRegistryAdapter, ArtifactRegistryGQLNode
]


@dataclass(frozen=True)
class ReadingById(When[ARegistryAndACaller, ArtifactRegistryAdapter, ArtifactRegistryGQLNode]):
    missing: bool = False

    @override
    def operation(self) -> str:
        return "get_registry_meta"

    @override
    def describe(self, laid: ARegistryAndACaller) -> str:
        who = laid.caller.username
        if self.missing:
            return Says(
                f"{who}이 어떤 레지스트리도 가리키지 않는 id 로 읽습니다",
                english=f"{who} reads by an id that names no registry",
            )
        return Says(
            f"{who}이 {laid.registry.name}을 id 로 읽습니다",
            english=f"{who} reads {laid.registry.name} by id",
        )

    @override
    async def call(
        self, adapter: ArtifactRegistryAdapter, laid: ARegistryAndACaller
    ) -> ArtifactRegistryGQLNode:
        registry_id = MISSING if self.missing else laid.registry.id
        with ActingAs(laid.caller):
            return await adapter.get_registry_meta(registry_id=registry_id)


@dataclass(frozen=True)
class ReadingByAnUnknownName(
    When[ARegistryAndACaller, ArtifactRegistryAdapter, ArtifactRegistryGQLNode]
):
    @override
    def operation(self) -> str:
        return "get_registry_meta"

    @override
    def describe(self, laid: ARegistryAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 어떤 레지스트리도 가리키지 않는 이름으로 읽습니다",
            english=f"{laid.caller.username} reads by a name that names no registry",
        )

    @override
    async def call(
        self, adapter: ArtifactRegistryAdapter, laid: ARegistryAndACaller
    ) -> ArtifactRegistryGQLNode:
        with ActingAs(laid.caller):
            return await adapter.get_registry_meta(registry_name=UNKNOWN_NAME)


@dataclass(frozen=True)
class ReadingWithoutAKey(
    When[ARegistryAndACaller, ArtifactRegistryAdapter, ArtifactRegistryGQLNode]
):
    @override
    def operation(self) -> str:
        return "get_registry_meta"

    @override
    def describe(self, laid: ARegistryAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 id 도 이름도 없이 읽습니다",
            english=f"{laid.caller.username} reads with neither an id nor a name",
        )

    @override
    async def call(
        self, adapter: ArtifactRegistryAdapter, laid: ARegistryAndACaller
    ) -> ArtifactRegistryGQLNode:
        with ActingAs(laid.caller):
            return await adapter.get_registry_meta()


@dataclass(frozen=True)
class AUserGrantedReadReadsARegistryById(
    Scenario[
        TestSeedingSession, ARegistryAndACaller, ArtifactRegistryAdapter, ArtifactRegistryGQLNode
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-read-reads-a-registry-by-id"

    @override
    def describe(self) -> str:
        return Says(
            "global 에서 아티팩트 레지스트리 읽기 권한을 받은 사용자가 레지스트리를 id 로 읽으면, "
            "미리 저장한 레지스트리 전체가 옵니다",
            english=(
                "when a user granted read permission on artifact registries in global reads a "
                "registry by id, the whole registry made in advance comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ARegistryAndACaller]:
        return ARegistryAndSomeone(role=UserRole.USER, granted=(Permission.READ,))

    @override
    def when(
        self,
    ) -> When[ARegistryAndACaller, ArtifactRegistryAdapter, ArtifactRegistryGQLNode]:
        return ReadingById()

    @override
    def then(self) -> Then[ARegistryAndACaller, ArtifactRegistryGQLNode]:
        return TheRegistryNode()


@dataclass(frozen=True)
class AUserGrantedNothingMayNotReadARegistry(
    Scenario[
        TestSeedingSession, ARegistryAndACaller, ArtifactRegistryAdapter, ArtifactRegistryGQLNode
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-read-a-registry"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 레지스트리를 id 로 읽으려 하면 권한 부족으로 "
            "거부됩니다",
            english=(
                "when a user granted nothing tries to read a registry by id, it is rejected for "
                "lack of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ARegistryAndACaller]:
        return ARegistryAndSomeone(role=UserRole.USER)

    @override
    def when(
        self,
    ) -> When[ARegistryAndACaller, ArtifactRegistryAdapter, ArtifactRegistryGQLNode]:
        return ReadingById()

    @override
    def then(self) -> Then[ARegistryAndACaller, ArtifactRegistryGQLNode]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AnIdNamingNoRegistryIsRefused(
    Scenario[
        TestSeedingSession, ARegistryAndACaller, ArtifactRegistryAdapter, ArtifactRegistryGQLNode
    ]
):
    @override
    def summary(self) -> str:
        return "an-id-naming-no-registry-is-refused"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 어떤 레지스트리도 가리키지 않는 id 로 읽으면, 그 레지스트리가 없다는 "
            "것으로 거부됩니다",
            english=(
                "when the superadmin reads by an id that names no registry, it is rejected as no "
                "such registry"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ARegistryAndACaller]:
        return ARegistryAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(
        self,
    ) -> When[ARegistryAndACaller, ArtifactRegistryAdapter, ArtifactRegistryGQLNode]:
        return ReadingById(missing=True)

    @override
    def then(self) -> Then[ARegistryAndACaller, ArtifactRegistryGQLNode]:
        return TheCallIsRefused(ArtifactRegistryNotFoundError)


@dataclass(frozen=True)
class ANameNamingNoRegistryIsRefused(
    Scenario[
        TestSeedingSession, ARegistryAndACaller, ArtifactRegistryAdapter, ArtifactRegistryGQLNode
    ]
):
    @override
    def summary(self) -> str:
        return "a-name-naming-no-registry-is-refused"

    @override
    def describe(self) -> str:
        return Says(
            "어떤 레지스트리도 가리키지 않는 이름으로 읽으면, 그 이름을 풀 수 없다는 것으로 "
            "거부됩니다",
            english=(
                "reading by a name that names no registry is rejected as the name not being "
                "resolvable"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ARegistryAndACaller]:
        return ARegistryAndSomeone(role=UserRole.USER)

    @override
    def when(
        self,
    ) -> When[ARegistryAndACaller, ArtifactRegistryAdapter, ArtifactRegistryGQLNode]:
        return ReadingByAnUnknownName()

    @override
    def then(self) -> Then[ARegistryAndACaller, ArtifactRegistryGQLNode]:
        return TheCallIsRefused(EntityNotFoundError)


@dataclass(frozen=True)
class ReadingWithoutAKeyIsRefused(
    Scenario[
        TestSeedingSession, ARegistryAndACaller, ArtifactRegistryAdapter, ArtifactRegistryGQLNode
    ]
):
    @override
    def summary(self) -> str:
        return "reading-a-registry-with-neither-an-id-nor-a-name-is-refused"

    @override
    def describe(self) -> str:
        return Says(
            "id 도 이름도 없이 레지스트리를 읽으려 하면, 요청 인자가 잘못됐다는 것으로 거부됩니다",
            english=(
                "reading a registry with neither an id nor a name is rejected as invalid request "
                "parameters"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ARegistryAndACaller]:
        return ARegistryAndSomeone(role=UserRole.USER)

    @override
    def when(
        self,
    ) -> When[ARegistryAndACaller, ArtifactRegistryAdapter, ArtifactRegistryGQLNode]:
        return ReadingWithoutAKey()

    @override
    def then(self) -> Then[ARegistryAndACaller, ArtifactRegistryGQLNode]:
        return TheCallIsRefused(InvalidAPIParameters)


SCENARIOS: list[RegistryStep] = [
    AUserGrantedReadReadsARegistryById(),
    AUserGrantedNothingMayNotReadARegistry(),
    AnIdNamingNoRegistryIsRefused(),
    ANameNamingNoRegistryIsRefused(),
    ReadingWithoutAKeyIsRefused(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_reading(
    scenario: RegistryStep,
    adapter: ArtifactRegistryAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
