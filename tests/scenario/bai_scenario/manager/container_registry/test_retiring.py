"""컨테이너 레지스트리와 허용 프로젝트 관계의 영구 삭제."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import override
from uuid import UUID

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.container_registry.request import (
    DeleteContainerRegistryInput,
)
from ai.backend.common.dto.manager.v2.container_registry.response import (
    DeleteContainerRegistryPayload,
)
from ai.backend.manager.api.adapters.container_registry.adapter import ContainerRegistryAdapter
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.errors.image import ContainerRegistryNotFound
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    SameAs,
    Scenario,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.answers import MissingResponse, TheCallIsRefused
from bai_scenario.components.container_registry import (
    ARegistryAndACaller,
    ARegistryAndSomeone,
    MissingRegistry,
    RegistryTarget,
    SeededRegistry,
    allowed_project_count,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

type DeletionScenario = Scenario[
    SeedingSession,
    ARegistryAndACaller,
    ContainerRegistryAdapter,
    DeleteContainerRegistryPayload,
]


@dataclass(frozen=True)
class Deleting(When[ARegistryAndACaller, ContainerRegistryAdapter, DeleteContainerRegistryPayload]):
    target: RegistryTarget = field(default_factory=SeededRegistry)

    @override
    def operation(self) -> str:
        return "admin_delete"

    @override
    def describe(self, laid: ARegistryAndACaller) -> str:
        return f"{laid.caller.username}이 {self.target.says()}를 삭제"

    @override
    async def call(
        self, adapter: ContainerRegistryAdapter, laid: ARegistryAndACaller
    ) -> DeleteContainerRegistryPayload:
        registry_id = self.target.id_of(laid)
        with ActingAs(laid.caller):
            return await adapter.admin_delete(DeleteContainerRegistryInput(id=registry_id))


@dataclass(frozen=True)
class TheDeletedIdComesBack(Then[ARegistryAndACaller, DeleteContainerRegistryPayload]):
    @override
    def says(self) -> str:
        return "삭제한 id가 반환된다"

    @override
    def look(
        self, laid: ARegistryAndACaller, answered: Answered[DeleteContainerRegistryPayload]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [MissingResponse(answered.raised)]
        wanted: UUID = laid.registry.id
        return [Held("id", payload.id, SameAs(wanted, "미리 만들어 둔 레지스트리의 id"))]


@dataclass(frozen=True)
class DeletingAnswersWithTheRemovedId(
    Scenario[
        SeedingSession,
        ARegistryAndACaller,
        ContainerRegistryAdapter,
        DeleteContainerRegistryPayload,
    ]
):
    @override
    def summary(self) -> str:
        return "deleting-a-registry-answers-with-the-id-it-removed"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 레지스트리를 삭제하면 삭제한 id를 담은 응답이 반환된다"

    @override
    def given(self) -> Given[SeedingSession, ARegistryAndACaller]:
        return ARegistryAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(
        self,
    ) -> When[ARegistryAndACaller, ContainerRegistryAdapter, DeleteContainerRegistryPayload]:
        return Deleting()

    @override
    def then(self) -> Then[ARegistryAndACaller, DeleteContainerRegistryPayload]:
        return TheDeletedIdComesBack()


@dataclass(frozen=True)
class DeletingTakesTheAllowedProjectWithIt(
    Scenario[
        SeedingSession,
        ARegistryAndACaller,
        ContainerRegistryAdapter,
        DeleteContainerRegistryPayload,
    ]
):
    @override
    def summary(self) -> str:
        return "deleting-a-registry-takes-its-allowed-projects-with-it"

    @override
    def describe(self) -> str:
        return "허용 프로젝트가 있는 레지스트리를 삭제하면, 외래 키를 통해 그 허용 목록까지 함께 삭제된다"

    @override
    def given(self) -> Given[SeedingSession, ARegistryAndACaller]:
        return ARegistryAndSomeone(role=UserRole.SUPERADMIN, allowed=True)

    @override
    def when(
        self,
    ) -> When[ARegistryAndACaller, ContainerRegistryAdapter, DeleteContainerRegistryPayload]:
        return Deleting()

    @override
    def then(self) -> Then[ARegistryAndACaller, DeleteContainerRegistryPayload]:
        return TheDeletedIdComesBack()


@dataclass(frozen=True)
class MissingRegistryIsRefused(
    Scenario[
        SeedingSession,
        ARegistryAndACaller,
        ContainerRegistryAdapter,
        DeleteContainerRegistryPayload,
    ]
):
    @override
    def summary(self) -> str:
        return "deleting-an-id-that-holds-no-registry-is-refused"

    @override
    def describe(self) -> str:
        return "존재하지 않는 id를 삭제하려 하면 대상을 찾을 수 없어 거부된다"

    @override
    def given(self) -> Given[SeedingSession, ARegistryAndACaller]:
        return ARegistryAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(
        self,
    ) -> When[ARegistryAndACaller, ContainerRegistryAdapter, DeleteContainerRegistryPayload]:
        return Deleting(target=MissingRegistry())

    @override
    def then(self) -> Then[ARegistryAndACaller, DeleteContainerRegistryPayload]:
        return TheCallIsRefused(ContainerRegistryNotFound)


@dataclass(frozen=True)
class APlainUserMayNotDelete(
    Scenario[
        SeedingSession,
        ARegistryAndACaller,
        ContainerRegistryAdapter,
        DeleteContainerRegistryPayload,
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-may-not-delete-a-registry"

    @override
    def describe(self) -> str:
        return (
            "슈퍼관리자가 아닌 사용자가 레지스트리를 삭제하려 하면 권한 부족으로 거부된다. "
            "이 호출은 호출자가 슈퍼관리자인지만 검사하고, 부여된 권한은 보지 않는다"
        )

    @override
    def given(self) -> Given[SeedingSession, ARegistryAndACaller]:
        return ARegistryAndSomeone()

    @override
    def when(
        self,
    ) -> When[ARegistryAndACaller, ContainerRegistryAdapter, DeleteContainerRegistryPayload]:
        return Deleting()

    @override
    def then(self) -> Then[ARegistryAndACaller, DeleteContainerRegistryPayload]:
        return TheCallIsRefused(InsufficientPrivilege)


SCENARIOS: list[DeletionScenario] = [
    DeletingAnswersWithTheRemovedId(),
    DeletingTakesTheAllowedProjectWithIt(),
    MissingRegistryIsRefused(),
    APlainUserMayNotDelete(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_retiring(
    scenario: DeletionScenario,
    adapter: ContainerRegistryAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
    assert await allowed_project_count(engine) == 0
