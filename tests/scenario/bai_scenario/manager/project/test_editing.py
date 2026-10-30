"""프로젝트 수정 — deprecated 활성 플래그가 soft delete 와 restore 로 가는가."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override

import pytest

from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.group.request import UpdateProjectInput
from ai.backend.common.dto.manager.v2.group.response import ProjectNode
from ai.backend.manager.api.adapters.project.adapter import ProjectAdapter
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Refused,
    Scenario,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.project import (
    ManyProjectsAndACaller,
    ManyProjectsAndSomeone,
    ProjectLook,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type ProjectStep = Scenario[TestSeedingSession, ManyProjectsAndACaller, ProjectAdapter, ProjectNode]


@dataclass(frozen=True)
class Editing(When[ManyProjectsAndACaller, ProjectAdapter, ProjectNode]):
    """미리 만든 프로젝트를 고친다. `soft_deleted`면 그 전에 soft delete 한다."""

    asked: UpdateProjectInput
    changing: str
    soft_deleted: bool = False

    @override
    def operation(self) -> str:
        return "update"

    @override
    def describe(self, laid: ManyProjectsAndACaller) -> str:
        (project,) = laid.targets
        before = " soft delete 한 뒤" if self.soft_deleted else ""
        return f"{laid.caller.username}이 {project.name}을{before} {self.changing}을 고침"

    @override
    async def call(self, adapter: ProjectAdapter, laid: ManyProjectsAndACaller) -> ProjectNode:
        (project,) = laid.targets
        project_id = ProjectID(project.id)
        with ActingAs(laid.caller):
            if self.soft_deleted:
                await adapter.delete(project_id)
            payload = await adapter.update(project_id, self.asked)
        return payload.project


@dataclass(frozen=True)
class TheProjectNode(Then[ManyProjectsAndACaller, ProjectNode]):
    """미리 만든 프로젝트 노드 하나가 통째로 온다."""

    started: datetime
    active: bool

    @override
    def says(self) -> str:
        return "미리 만든 프로젝트 전체가 온다"

    @override
    def look(self, laid: ManyProjectsAndACaller, answered: Answered[ProjectNode]) -> list[Verdict]:
        node = answered.response
        if node is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        (project,) = laid.targets
        return ProjectLook(self.started, active=self.active).verdicts("", node, project)


@dataclass(frozen=True)
class ClearingTheActiveFlagSoftDeletes(
    Scenario[TestSeedingSession, ManyProjectsAndACaller, ProjectAdapter, ProjectNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "clearing-the-active-flag-soft-deletes-a-project"

    @override
    def describe(self) -> str:
        return (
            "활성 플래그를 내리는 수정은 프로젝트를 soft delete 하고, 답이 비활성 상태를 실어 온다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyProjectsAndACaller]:
        return ManyProjectsAndSomeone(role=UserRole.SUPERADMIN, count=1)

    @override
    def when(self) -> When[ManyProjectsAndACaller, ProjectAdapter, ProjectNode]:
        return Editing(UpdateProjectInput(is_active=False), changing="활성 플래그")

    @override
    def then(self) -> Then[ManyProjectsAndACaller, ProjectNode]:
        return TheProjectNode(started=self.started, active=False)


@dataclass(frozen=True)
class RaisingTheActiveFlagRestores(
    Scenario[TestSeedingSession, ManyProjectsAndACaller, ProjectAdapter, ProjectNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "raising-the-active-flag-restores-a-soft-deleted-project"

    @override
    def describe(self) -> str:
        return (
            "soft delete 된 프로젝트의 활성 플래그를 올리는 수정은 그 프로젝트를 restore 하고, "
            "답이 활성 상태를 실어 온다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyProjectsAndACaller]:
        return ManyProjectsAndSomeone(role=UserRole.SUPERADMIN, count=1)

    @override
    def when(self) -> When[ManyProjectsAndACaller, ProjectAdapter, ProjectNode]:
        return Editing(
            UpdateProjectInput(is_active=True), changing="활성 플래그", soft_deleted=True
        )

    @override
    def then(self) -> Then[ManyProjectsAndACaller, ProjectNode]:
        return TheProjectNode(started=self.started, active=True)


SCENARIOS: list[ProjectStep] = [
    ClearingTheActiveFlagSoftDeletes(started=datetime.now(UTC)),
    RaisingTheActiveFlagRestores(started=datetime.now(UTC)),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_editing(
    scenario: ProjectStep, adapter: ProjectAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
