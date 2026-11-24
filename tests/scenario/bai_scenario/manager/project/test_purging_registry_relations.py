"""프로젝트와 레지스트리 사이의 relation 지우기: 두 스코프의 권한, 없는 relation, default 레지스트리."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import pytest
import sqlalchemy as sa

from ai.backend.common.dto.manager.v2.group.request import (
    ProjectContainerRegistryRelationInput,
    PurgeProjectContainerRegistryRelationsInput,
)
from ai.backend.common.dto.manager.v2.group.response import (
    ProjectContainerRegistryRelation,
    PurgeProjectContainerRegistryRelationsPayload,
)
from ai.backend.manager.api.adapters.project.adapter import ProjectAdapter
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
    ARegistryAndAProjectToAllow,
    ARegistryToAllowAndACaller,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Laid = ARegistryToAllowAndACaller
type Purged = PurgeProjectContainerRegistryRelationsPayload
type PurgeScenario = Scenario[TestSeedingSession, Laid, ProjectAdapter, Purged]


@dataclass(frozen=True)
class PurgingRelations(When[Laid, ProjectAdapter, Purged]):
    @override
    def operation(self) -> str:
        return "purge_container_registry_relations"

    @override
    def describe(self, laid: Laid) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.project.name}과 그 레지스트리 사이의 relation을 지웁니다",
            english=(
                f"{laid.caller.username} purges the relation between {laid.project.name} and "
                "that registry"
            ),
        )

    @override
    async def call(self, adapter: ProjectAdapter, laid: Laid) -> Purged:
        with ActingAs(laid.caller):
            return await adapter.purge_container_registry_relations(
                PurgeProjectContainerRegistryRelationsInput(
                    items=[
                        ProjectContainerRegistryRelationInput(
                            project_id=laid.project.id, container_registry_id=laid.registry.id
                        )
                    ]
                )
            )


@dataclass(frozen=True)
class ThePurgedRelationsComeBack(Then[Laid, Purged]):
    """이번 요청이 지운 relation만 응답에 온다."""

    existed: bool

    @override
    def says(self) -> str:
        if self.existed:
            return Says(
                "지운 프로젝트와 레지스트리 relation 하나가 옵니다",
                english="the purged project and registry relation comes back",
            )
        return Says("빈 목록이 옵니다", english="an empty list comes back")

    @override
    def look(self, laid: Laid, answered: Answered[Purged]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        if not self.existed:
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
class AUserGrantedOnBothScopesPurgesARelation(
    Scenario[TestSeedingSession, Laid, ProjectAdapter, Purged]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-on-both-scopes-purges-a-project-registry-relation"

    @override
    def describe(self) -> str:
        return Says(
            "프로젝트와 레지스트리 두 스코프 모두에 권한을 받은 사용자는 그 프로젝트와 레지스트리 사이의 relation을 지울 수 있습니다",
            english=(
                "a user granted permission on both the project and the registry scopes can "
                "purge the relation between them"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, Laid]:
        return ARegistryAndAProjectToAllow(allowed=True)

    @override
    def when(self) -> When[Laid, ProjectAdapter, Purged]:
        return PurgingRelations()

    @override
    def then(self) -> Then[Laid, Purged]:
        return ThePurgedRelationsComeBack(existed=True)


@dataclass(frozen=True)
class AUserGrantedOnTheRegistryAloneMayNotPurgeARelation(
    Scenario[TestSeedingSession, Laid, ProjectAdapter, Purged]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-on-the-registry-alone-may-not-purge-a-project-registry-relation"

    @override
    def describe(self) -> str:
        return Says(
            "레지스트리에만 권한을 받은 사용자가 프로젝트와 그 레지스트리 사이의 relation을 지우려 하면 거부됩니다",
            english=(
                "a user granted permission on the registry alone is refused when purging "
                "the relation between a project and it"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, Laid]:
        return ARegistryAndAProjectToAllow(on_project=False, allowed=True)

    @override
    def when(self) -> When[Laid, ProjectAdapter, Purged]:
        return PurgingRelations()

    @override
    def then(self) -> Then[Laid, Any]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class PurgingAMissingRelationLeavesItOut(
    Scenario[TestSeedingSession, Laid, ProjectAdapter, Purged]
):
    @override
    def summary(self) -> str:
        return "purging-a-relation-that-does-not-exist-leaves-it-out-of-the-response"

    @override
    def describe(self) -> str:
        return Says(
            "없는 relation을 지워도 거부되지 않고, 응답에서는 빠집니다",
            english=(
                "purging a relation that does not exist is not refused, and the relation is "
                "left out of the response"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, Laid]:
        return ARegistryAndAProjectToAllow()

    @override
    def when(self) -> When[Laid, ProjectAdapter, Purged]:
        return PurgingRelations()

    @override
    def then(self) -> Then[Laid, Purged]:
        return ThePurgedRelationsComeBack(existed=False)


@dataclass(frozen=True)
class PurgingTheDefaultRelationIsNotRefused(
    Scenario[TestSeedingSession, Laid, ProjectAdapter, Purged]
):
    @override
    def summary(self) -> str:
        return "purging-the-relation-to-the-default-registry-is-not-refused"

    @override
    def describe(self) -> str:
        return Says(
            "프로젝트의 default 레지스트리와의 relation도 거부되지 않고 지워집니다",
            english=(
                "the relation to the project's default registry is purged without being refused"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, Laid]:
        return ARegistryAndAProjectToAllow(allowed_as_default=True)

    @override
    def when(self) -> When[Laid, ProjectAdapter, Purged]:
        return PurgingRelations()

    @override
    def then(self) -> Then[Laid, Purged]:
        return ThePurgedRelationsComeBack(existed=True)


SCENARIOS: list[PurgeScenario] = [
    AUserGrantedOnBothScopesPurgesARelation(),
    AUserGrantedOnTheRegistryAloneMayNotPurgeARelation(),
    PurgingAMissingRelationLeavesItOut(),
    PurgingTheDefaultRelationIsNotRefused(),
]


def expected_relation_count(scenario: PurgeScenario) -> int:
    match scenario:
        case AUserGrantedOnTheRegistryAloneMayNotPurgeARelation():
            return 1
        case _:
            return 0


async def relation_count(engine: ExtendedAsyncSAEngine) -> int:
    async with engine.begin_readonly_session() as session:
        query = sa.select(sa.func.count()).select_from(AssociationContainerRegistriesGroupsRow)
        return int(await session.scalar(query) or 0)


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_purging_registry_relations(
    scenario: PurgeScenario, adapter: ProjectAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
    assert await relation_count(engine) == expected_relation_count(scenario)
