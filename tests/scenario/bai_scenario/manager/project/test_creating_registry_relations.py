"""프로젝트와 레지스트리 사이에 relation 만들기: 두 스코프의 권한, 이미 있는 relation, 없는 레지스트리."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import pytest
import sqlalchemy as sa

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.group.request import (
    CreateProjectContainerRegistryRelationsInput,
    ProjectContainerRegistryRelationInput,
)
from ai.backend.common.dto.manager.v2.group.response import (
    CreateProjectContainerRegistryRelationsPayload,
    ProjectContainerRegistryRelation,
)
from ai.backend.manager.api.adapters.project.adapter import ProjectAdapter
from ai.backend.manager.errors.image import ContainerRegistryNotFound
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.association_container_registries_groups.row import (
    AssociationContainerRegistriesGroupsRow,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    Refused,
    Same,
    SameAs,
    Says,
    Scenario,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.container_registry import (
    MISSING_ENTITY_ID,
    ARegistryAndAProjectToAllow,
    ARegistryToAllowAndACaller,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Laid = ARegistryToAllowAndACaller
type Created = CreateProjectContainerRegistryRelationsPayload
type CreateScenario = Scenario[TestSeedingSession, Laid, ProjectAdapter, Created]


@dataclass(frozen=True)
class CreatingRelations(When[Laid, ProjectAdapter, Created]):
    missing_registry: bool = False

    @override
    def operation(self) -> str:
        return "create_container_registry_relations"

    @override
    def describe(self, laid: Laid) -> str:
        if self.missing_registry:
            return Says(
                f"{laid.caller.username}이 {laid.project.name}과 존재하지 않는 레지스트리 사이에 relation을 만듭니다",
                english=(
                    f"{laid.caller.username} creates a relation between {laid.project.name} and a "
                    "registry that does not exist"
                ),
            )
        return Says(
            f"{laid.caller.username}이 {laid.project.name}과 그 레지스트리 사이에 relation을 만듭니다",
            english=(
                f"{laid.caller.username} creates a relation between {laid.project.name} and "
                "that registry"
            ),
        )

    @override
    async def call(self, adapter: ProjectAdapter, laid: Laid) -> Created:
        with ActingAs(laid.caller):
            return await adapter.create_container_registry_relations(
                CreateProjectContainerRegistryRelationsInput(
                    items=[
                        ProjectContainerRegistryRelationInput(
                            project_id=laid.project.id,
                            container_registry_id=(
                                MISSING_ENTITY_ID if self.missing_registry else laid.registry.id
                            ),
                        )
                    ]
                )
            )


@dataclass(frozen=True)
class TheCreatedRelationsComeBack(Then[Laid, Created]):
    """이번 요청이 새로 만든 relation만 응답에 온다."""

    newly_created: bool

    @override
    def says(self) -> str:
        if self.newly_created:
            return Says(
                "새로 만든 프로젝트와 레지스트리 relation 하나가 옵니다",
                english="the newly created project and registry relation comes back",
            )
        return Says("빈 목록이 옵니다", english="an empty list comes back")

    @override
    def look(self, laid: Laid, answered: Answered[Created]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        if not self.newly_created:
            return [Same[list[ProjectContainerRegistryRelation]]("items", payload.items, [])]
        requested = ProjectContainerRegistryRelation(
            project_id=laid.project.id, container_registry_id=laid.registry.id
        )
        return [
            Held[list[ProjectContainerRegistryRelation]](
                "items",
                payload.items,
                SameAs(
                    [requested],
                    Says(
                        "요청한 프로젝트와 레지스트리 한 쌍",
                        english="the requested project and registry pair",
                    ),
                ),
            )
        ]


@dataclass(frozen=True)
class AUserGrantedOnBothScopesCreatesARelation(
    Scenario[TestSeedingSession, Laid, ProjectAdapter, Created]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-on-both-scopes-creates-a-project-registry-relation"

    @override
    def describe(self) -> str:
        return Says(
            "프로젝트와 레지스트리 두 스코프 모두에 권한을 받은 사용자는 그 프로젝트와 레지스트리 사이에 relation을 만들 수 있습니다",
            english=(
                "a user granted permission on both the project and the registry scopes can "
                "create a relation between them"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, Laid]:
        return ARegistryAndAProjectToAllow()

    @override
    def when(self) -> When[Laid, ProjectAdapter, Created]:
        return CreatingRelations()

    @override
    def then(self) -> Then[Laid, Created]:
        return TheCreatedRelationsComeBack(newly_created=True)


@dataclass(frozen=True)
class AUserGrantedOnTheRegistryAloneMayNotCreateARelation(
    Scenario[TestSeedingSession, Laid, ProjectAdapter, Created]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-on-the-registry-alone-may-not-create-a-project-registry-relation"

    @override
    def describe(self) -> str:
        return Says(
            "레지스트리에만 권한을 받은 사용자가 프로젝트와 그 레지스트리 사이에 relation을 만들려 하면 거부됩니다",
            english=(
                "a user granted permission on the registry alone is refused when creating "
                "a relation between a project and it"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, Laid]:
        return ARegistryAndAProjectToAllow(on_project=False)

    @override
    def when(self) -> When[Laid, ProjectAdapter, Created]:
        return CreatingRelations()

    @override
    def then(self) -> Then[Laid, Any]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class CreatingAnExistingRelationLeavesItOut(
    Scenario[TestSeedingSession, Laid, ProjectAdapter, Created]
):
    @override
    def summary(self) -> str:
        return "creating-an-existing-relation-leaves-it-out-of-the-response"

    @override
    def describe(self) -> str:
        return Says(
            "이미 있는 relation을 다시 만들어도 거부되지 않고, 응답에서는 빠집니다",
            english=(
                "creating a relation that already exists is not refused, and the relation "
                "is left out of the response"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, Laid]:
        return ARegistryAndAProjectToAllow(allowed=True)

    @override
    def when(self) -> When[Laid, ProjectAdapter, Created]:
        return CreatingRelations()

    @override
    def then(self) -> Then[Laid, Created]:
        return TheCreatedRelationsComeBack(newly_created=False)


@dataclass(frozen=True)
class CreatingARelationToAMissingRegistryIsRefused(
    Scenario[TestSeedingSession, Laid, ProjectAdapter, Created]
):
    @override
    def summary(self) -> str:
        return "a-superadmin-naming-a-registry-that-does-not-exist-is-refused"

    @override
    def describe(self) -> str:
        return Says(
            "프로젝트와 존재하지 않는 레지스트리 사이에 relation을 만들려 하면 그 레지스트리가 없다는 "
            "이유로 거부됩니다",
            english=(
                "creating a relation between a project and a registry that does not exist is "
                "refused because there is no such registry"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, Laid]:
        return ARegistryAndAProjectToAllow(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[Laid, ProjectAdapter, Created]:
        return CreatingRelations(missing_registry=True)

    @override
    def then(self) -> Then[Laid, Any]:
        return TheCallIsRefused(ContainerRegistryNotFound)


SCENARIOS: list[CreateScenario] = [
    AUserGrantedOnBothScopesCreatesARelation(),
    AUserGrantedOnTheRegistryAloneMayNotCreateARelation(),
    CreatingAnExistingRelationLeavesItOut(),
    CreatingARelationToAMissingRegistryIsRefused(),
]


def expected_relation_count(scenario: CreateScenario) -> int:
    match scenario:
        case (
            AUserGrantedOnTheRegistryAloneMayNotCreateARelation()
            | CreatingARelationToAMissingRegistryIsRefused()
        ):
            return 0
        case _:
            return 1


async def relation_count(engine: ExtendedAsyncSAEngine) -> int:
    async with engine.begin_readonly_session() as session:
        query = sa.select(sa.func.count()).select_from(AssociationContainerRegistriesGroupsRow)
        return int(await session.scalar(query) or 0)


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_creating_registry_relations(
    scenario: CreateScenario, adapter: ProjectAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
    assert await relation_count(engine) == expected_relation_count(scenario)
