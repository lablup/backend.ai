"""프로젝트가 따르는 정책 읽기 — 그 프로젝트 범위에서만 읽는다."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override

import pytest

from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.dto.manager.v2.resource_policy.response import ProjectResourcePolicyNode
from ai.backend.manager.api.adapters.resource_policy.adapter import ResourcePolicyAdapter
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Says, Scenario, Then, When
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.resource_policy import (
    AProjectAndSomeone,
    AProjectPolicyAndACaller,
    TheProjectPolicyNode,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type ReadingStep = Scenario[
    TestSeedingSession, AProjectPolicyAndACaller, ResourcePolicyAdapter, ProjectResourcePolicyNode
]


@dataclass(frozen=True)
class ReadingTheProjectPolicy(
    When[AProjectPolicyAndACaller, ResourcePolicyAdapter, ProjectResourcePolicyNode]
):
    """그 프로젝트가 따르는 정책을 그 프로젝트의 범위에서 읽는다."""

    @override
    def operation(self) -> str:
        return "get_project_resource_policy"

    @override
    def describe(self, laid: AProjectPolicyAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.project.name} 프로젝트의 정책을 읽습니다",
            english=f"{laid.caller.username} reads the policy of the project {laid.project.name}",
        )

    @override
    async def call(
        self, adapter: ResourcePolicyAdapter, laid: AProjectPolicyAndACaller
    ) -> ProjectResourcePolicyNode:
        with ActingAs(laid.caller):
            return await adapter.get_project_resource_policy(ProjectID(laid.project.id))


@dataclass(frozen=True)
class AUserGrantedReadInTheProjectReadsIt(
    Scenario[
        TestSeedingSession,
        AProjectPolicyAndACaller,
        ResourcePolicyAdapter,
        ProjectResourcePolicyNode,
    ]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-read-in-the-project-reads-its-resource-policy"

    @override
    def describe(self) -> str:
        return Says(
            "그 프로젝트 범위에서 프로젝트 정책 읽기 권한을 받은 사용자가 조회하면, 그 "
            "프로젝트가 따르는 정책 전체가 반환됩니다",
            english=(
                "a user granted permission to read project resource policies in the project's "
                "scope gets the whole policy that project follows"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AProjectPolicyAndACaller]:
        return AProjectAndSomeone()

    @override
    def when(
        self,
    ) -> When[AProjectPolicyAndACaller, ResourcePolicyAdapter, ProjectResourcePolicyNode]:
        return ReadingTheProjectPolicy()

    @override
    def then(self) -> Then[AProjectPolicyAndACaller, ProjectResourcePolicyNode]:
        return TheProjectPolicyNode(self.started)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotReadIt(
    Scenario[
        TestSeedingSession,
        AProjectPolicyAndACaller,
        ResourcePolicyAdapter,
        ProjectResourcePolicyNode,
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-read-a-projects-resource-policy"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 프로젝트가 따르는 정책을 조회하면, 그 프로젝트 "
            "범위에 권한이 없으므로 거부됩니다",
            english=(
                "a user granted nothing reading the policy a project follows is rejected because "
                "they hold no permission in that project's scope"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AProjectPolicyAndACaller]:
        return AProjectAndSomeone(granted=False)

    @override
    def when(
        self,
    ) -> When[AProjectPolicyAndACaller, ResourcePolicyAdapter, ProjectResourcePolicyNode]:
        return ReadingTheProjectPolicy()

    @override
    def then(self) -> Then[AProjectPolicyAndACaller, ProjectResourcePolicyNode]:
        return TheCallIsRefused(NotEnoughPermission)


SCENARIOS: list[ReadingStep] = [
    AUserGrantedReadInTheProjectReadsIt(started=datetime.now(UTC)),
    AUserGrantedNothingMayNotReadIt(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_reading_project_policy(
    scenario: ReadingStep, adapter: ResourcePolicyAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
