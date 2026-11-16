"""프로젝트 fair share 가중치 여럿 한 번에 정하기."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import pytest

from ai.backend.common.data.permission.types import Permission
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.fair_share.request import (
    BulkUpsertProjectFairShareWeightInput,
    ProjectWeightEntryInput,
)
from ai.backend.common.dto.manager.v2.fair_share.response import (
    BulkUpsertProjectFairShareWeightPayload,
)
from ai.backend.manager.api.adapters.fair_share.adapter import FairShareAdapter
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Says, Scenario, Then, When
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.fair_share import (
    WEIGHT,
    EveryProjectWeightIsWritten,
    ProjectsInAGroupAndACaller,
    ProjectsInAGroupAndSomeone,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Upserted = BulkUpsertProjectFairShareWeightPayload
type FairShareStep = Scenario[TestSeedingSession, ProjectsInAGroupAndACaller, FairShareAdapter, Any]


@dataclass(frozen=True)
class Setting(When[ProjectsInAGroupAndACaller, FairShareAdapter, Upserted]):
    """그룹 안 프로젝트의 가중치를 정한다."""

    @override
    def operation(self) -> str:
        return "atomic_bulk_upsert_project"

    @override
    def describe(self, laid: ProjectsInAGroupAndACaller) -> str:
        return Says(
            (
                f"{laid.caller.username} 이 {laid.group.name} 안 프로젝트 {len(laid.projects)}개의 가중치를 한 번에 정합니다"
            ),
            english=f"{laid.caller.username} sets the weights of {len(laid.projects)} projects in {laid.group.name} at once",
        )

    @override
    async def call(self, adapter: FairShareAdapter, laid: ProjectsInAGroupAndACaller) -> Upserted:
        with ActingAs(laid.caller):
            return await adapter.atomic_bulk_upsert_project(
                BulkUpsertProjectFairShareWeightInput(
                    resource_group_name=laid.group.name,
                    inputs=[
                        ProjectWeightEntryInput(
                            project_id=item.id, domain_name=laid.domain.name, weight=WEIGHT
                        )
                        for item in laid.projects
                    ],
                )
            )


@dataclass(frozen=True)
class TheSuperadminSets(
    Scenario[TestSeedingSession, ProjectsInAGroupAndACaller, FairShareAdapter, Upserted]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-sets-several-project-weights-at-once"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 프로젝트 둘의 가중치를 한 번에 정하면 둘을 정했다는 개수가 옵니다",
            english="when the superadmin sets the weights of two projects at once, a count comes back saying that two were set",
        )

    @override
    def given(self) -> Given[TestSeedingSession, ProjectsInAGroupAndACaller]:
        return ProjectsInAGroupAndSomeone(role=UserRole.SUPERADMIN, besides=1)

    @override
    def when(self) -> When[ProjectsInAGroupAndACaller, FairShareAdapter, Upserted]:
        return Setting()

    @override
    def then(self) -> Then[ProjectsInAGroupAndACaller, Upserted]:
        return EveryProjectWeightIsWritten()


@dataclass(frozen=True)
class AUserGrantedUpdateOnTheGroupMayNotSet(
    Scenario[TestSeedingSession, ProjectsInAGroupAndACaller, FairShareAdapter, Upserted]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-update-on-the-group-may-not-set-several-project-weights"

    @override
    def describe(self) -> str:
        return Says(
            "그 그룹에 부여한 역할로 수정 권한을 받은 사용자가 프로젝트 둘의 가중치를 한 번에 정하려 하면 권한 부족으로 거부됩니다. 가중치 쓰기는 그룹이 아니라 전역 대상을 기준으로 권한을 검사합니다",
            english="when a user granted the update permission through a role assigned on the group tries to set the weights of two projects at once, it is rejected for a lack of permission. A weight write checks permission against the global target, not the group",
        )

    @override
    def given(self) -> Given[TestSeedingSession, ProjectsInAGroupAndACaller]:
        return ProjectsInAGroupAndSomeone(granted=Permission.UPDATE, besides=1)

    @override
    def when(self) -> When[ProjectsInAGroupAndACaller, FairShareAdapter, Upserted]:
        return Setting()

    @override
    def then(self) -> Then[ProjectsInAGroupAndACaller, Upserted]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotSet(
    Scenario[TestSeedingSession, ProjectsInAGroupAndACaller, FairShareAdapter, Upserted]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-set-several-project-weights"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 프로젝트 둘의 가중치를 한 번에 정하려 하면 권한 부족으로 거부됩니다",
            english="when a user granted nothing tries to set the weights of two projects at once, it is rejected for a lack of permission",
        )

    @override
    def given(self) -> Given[TestSeedingSession, ProjectsInAGroupAndACaller]:
        return ProjectsInAGroupAndSomeone(besides=1)

    @override
    def when(self) -> When[ProjectsInAGroupAndACaller, FairShareAdapter, Upserted]:
        return Setting()

    @override
    def then(self) -> Then[ProjectsInAGroupAndACaller, Upserted]:
        return TheCallIsRefused(NotEnoughPermission)


SCENARIOS: list[FairShareStep] = [
    TheSuperadminSets(),
    AUserGrantedUpdateOnTheGroupMayNotSet(),
    AUserGrantedNothingMayNotSet(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_atomic_bulk_upserting_projects(
    scenario: FairShareStep, adapter: FairShareAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
