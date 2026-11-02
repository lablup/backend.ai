"""컨테이너 레지스트리와 허용 프로젝트 관계의 영구 삭제."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import override
from uuid import UUID

import pytest

from ai.backend.common.data.entity.container_registry import ContainerRegistryID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.container_registry.response import (
    PurgeContainerRegistryPayload,
)
from ai.backend.manager.api.adapters.container_registry.adapter import ContainerRegistryAdapter
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.errors.image import ContainerRegistryNotFound
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    Language,
    SameAs,
    Says,
    Scenario,
    Then,
    Verdict,
    When,
    in_language,
)
from bai_scenario.components.answers import MissingResponse, TheCallIsRefused
from bai_scenario.components.container_registry import (
    ARegistryAndACaller,
    ARegistryAndSomeone,
    MissingRegistry,
    RegistryTarget,
    TestSeededRegistry,
    allowed_project_count,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type DeletionScenario = Scenario[
    TestSeedingSession,
    ARegistryAndACaller,
    ContainerRegistryAdapter,
    PurgeContainerRegistryPayload,
]


@dataclass(frozen=True)
class Deleting(When[ARegistryAndACaller, ContainerRegistryAdapter, PurgeContainerRegistryPayload]):
    target: RegistryTarget = field(default_factory=TestSeededRegistry)

    @override
    def operation(self) -> str:
        return "admin_purge"

    @override
    def describe(self, laid: ARegistryAndACaller) -> str:
        target = self.target.says()
        return Says(
            f"{laid.caller.username}이 {target}를 삭제합니다",
            english=f"{laid.caller.username} deletes {in_language(target, Language.ENGLISH)}",
        )

    @override
    async def call(
        self, adapter: ContainerRegistryAdapter, laid: ARegistryAndACaller
    ) -> PurgeContainerRegistryPayload:
        registry_id = self.target.id_of(laid)
        with ActingAs(laid.caller):
            return await adapter.admin_purge(ContainerRegistryID(registry_id))


@dataclass(frozen=True)
class TheDeletedIdComesBack(Then[ARegistryAndACaller, PurgeContainerRegistryPayload]):
    @override
    def says(self) -> str:
        return Says("삭제한 id 가 반환됩니다", english="the id that was deleted comes back")

    @override
    def look(
        self, laid: ARegistryAndACaller, answered: Answered[PurgeContainerRegistryPayload]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [MissingResponse(answered.raised)]
        wanted: UUID = laid.registry.id
        return [
            Held(
                "id",
                payload.id,
                SameAs(
                    wanted,
                    Says(
                        "미리 저장한 컨테이너 레지스트리의 id",
                        english="the id of the container registry seeded in advance",
                    ),
                ),
            )
        ]


@dataclass(frozen=True)
class DeletingAnswersWithTheRemovedId(
    Scenario[
        TestSeedingSession,
        ARegistryAndACaller,
        ContainerRegistryAdapter,
        PurgeContainerRegistryPayload,
    ]
):
    @override
    def summary(self) -> str:
        return "deleting-a-registry-answers-with-the-id-it-removed"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 컨테이너 레지스트리를 삭제하면 삭제한 id 를 담은 응답이 반환됩니다",
            english=(
                "when the superadmin deletes a container registry, the answer comes back "
                "holding the id it deleted"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ARegistryAndACaller]:
        return ARegistryAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(
        self,
    ) -> When[ARegistryAndACaller, ContainerRegistryAdapter, PurgeContainerRegistryPayload]:
        return Deleting()

    @override
    def then(self) -> Then[ARegistryAndACaller, PurgeContainerRegistryPayload]:
        return TheDeletedIdComesBack()


@dataclass(frozen=True)
class DeletingTakesTheAllowedProjectWithIt(
    Scenario[
        TestSeedingSession,
        ARegistryAndACaller,
        ContainerRegistryAdapter,
        PurgeContainerRegistryPayload,
    ]
):
    @override
    def summary(self) -> str:
        return "deleting-a-registry-takes-its-allowed-projects-with-it"

    @override
    def describe(self) -> str:
        return Says(
            "허용 프로젝트가 있는 컨테이너 레지스트리를 삭제하면, 외래 키를 통해 그 허용 목록까지 "
            "함께 삭제됩니다",
            english=(
                "when a container registry that has an allowed project is deleted, the allow "
                "list is deleted with it through the foreign key"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ARegistryAndACaller]:
        return ARegistryAndSomeone(role=UserRole.SUPERADMIN, allowed=True)

    @override
    def when(
        self,
    ) -> When[ARegistryAndACaller, ContainerRegistryAdapter, PurgeContainerRegistryPayload]:
        return Deleting()

    @override
    def then(self) -> Then[ARegistryAndACaller, PurgeContainerRegistryPayload]:
        return TheDeletedIdComesBack()


@dataclass(frozen=True)
class MissingRegistryIsRefused(
    Scenario[
        TestSeedingSession,
        ARegistryAndACaller,
        ContainerRegistryAdapter,
        PurgeContainerRegistryPayload,
    ]
):
    @override
    def summary(self) -> str:
        return "deleting-an-id-that-holds-no-registry-is-refused"

    @override
    def describe(self) -> str:
        return Says(
            "존재하지 않는 id 를 삭제하려 하면 대상을 찾을 수 없어 거부됩니다",
            english="when an id that does not exist is deleted, it is rejected because the target cannot be found",
        )

    @override
    def given(self) -> Given[TestSeedingSession, ARegistryAndACaller]:
        return ARegistryAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(
        self,
    ) -> When[ARegistryAndACaller, ContainerRegistryAdapter, PurgeContainerRegistryPayload]:
        return Deleting(target=MissingRegistry())

    @override
    def then(self) -> Then[ARegistryAndACaller, PurgeContainerRegistryPayload]:
        return TheCallIsRefused(ContainerRegistryNotFound)


@dataclass(frozen=True)
class APlainUserMayNotDelete(
    Scenario[
        TestSeedingSession,
        ARegistryAndACaller,
        ContainerRegistryAdapter,
        PurgeContainerRegistryPayload,
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-may-not-delete-a-registry"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 아닌 사용자가 컨테이너 레지스트리를 삭제하려 하면 권한 부족으로 "
            "거부됩니다. 이 호출은 호출자가 superadmin 인지만 검사하고 부여된 권한은 보지 않습니다",
            english=(
                "when a user who is not the superadmin tries to delete a container registry, "
                "it is rejected for lack of permission. This call checks only whether the "
                "caller is the superadmin and does not look at the permissions granted"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ARegistryAndACaller]:
        return ARegistryAndSomeone()

    @override
    def when(
        self,
    ) -> When[ARegistryAndACaller, ContainerRegistryAdapter, PurgeContainerRegistryPayload]:
        return Deleting()

    @override
    def then(self) -> Then[ARegistryAndACaller, PurgeContainerRegistryPayload]:
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
