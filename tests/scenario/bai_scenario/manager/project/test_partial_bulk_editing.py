"""프로젝트 여럿 수정하기."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.common import PartialBulkPayload
from ai.backend.common.dto.manager.v2.group.request import (
    PartialBulkUpdateProjectItemInput,
    PartialBulkUpdateProjectsInput,
    UpdateProjectInput,
)
from ai.backend.common.dto.manager.v2.group.response import ProjectNode
from ai.backend.manager.api.adapters.project.adapter import ProjectAdapter
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Refused,
    Same,
    Scenario,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.project import (
    ManyProjectsAndACaller,
    ManyProjectsAndSomeone,
    NoProjectIsProcessed,
    ProjectLook,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

EDITED = "한 번에 고친 설명"

type Edited = PartialBulkPayload[ProjectNode]
type ProjectStep = Scenario[TestSeedingSession, ManyProjectsAndACaller, ProjectAdapter, Edited]


@dataclass(frozen=True)
class EditingEveryTarget(When[ManyProjectsAndACaller, ProjectAdapter, Edited]):
    """대상 프로젝트들의 설명을 한 번에 고친다."""

    @override
    def operation(self) -> str:
        return "partial_bulk_update"

    @override
    def describe(self, laid: ManyProjectsAndACaller) -> str:
        return f"{laid.caller.username}이 프로젝트 {len(laid.targets)}개의 설명을 한 번에 고침"

    @override
    async def call(self, adapter: ProjectAdapter, laid: ManyProjectsAndACaller) -> Edited:
        with ActingAs(laid.caller):
            return await adapter.partial_bulk_update(
                PartialBulkUpdateProjectsInput(
                    items=[
                        PartialBulkUpdateProjectItemInput(
                            id=project.id, input=UpdateProjectInput(description=EDITED)
                        )
                        for project in laid.targets
                    ]
                )
            )


@dataclass(frozen=True)
class EveryTargetIsEdited(Then[ManyProjectsAndACaller, Edited]):
    """대상이 모두 새 설명을 싣고 처리된 목록에 오고, 실패 목록은 비어 있다."""

    started: datetime

    @override
    def says(self) -> str:
        return "대상 프로젝트가 모두 새 설명으로 오고, 실패한 것은 없다"

    @override
    def look(self, laid: ManyProjectsAndACaller, answered: Answered[Edited]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        look = ProjectLook(self.started, described=EDITED)
        verdicts: list[Verdict] = [
            Same("successes count", len(payload.successes), len(laid.targets)),
            Same("failed", payload.failed, []),
        ]
        for i, (node, project) in enumerate(zip(payload.successes, laid.targets, strict=False)):
            verdicts += look.verdicts(f"successes[{i}].", node, project)
        return verdicts


@dataclass(frozen=True)
class TheSuperadminEditsSeveralProjects(
    Scenario[TestSeedingSession, ManyProjectsAndACaller, ProjectAdapter, Edited]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-edits-several-projects-at-once"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 프로젝트 여럿의 설명을 한 번에 바꾸면, 모두 새 설명으로 오고 실패한 것은 없다"

    @override
    def given(self) -> Given[TestSeedingSession, ManyProjectsAndACaller]:
        return ManyProjectsAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyProjectsAndACaller, ProjectAdapter, Edited]:
        return EditingEveryTarget()

    @override
    def then(self) -> Then[ManyProjectsAndACaller, Edited]:
        return EveryTargetIsEdited(started=self.started)


@dataclass(frozen=True)
class AUserGrantedNothingEditsNone(
    Scenario[TestSeedingSession, ManyProjectsAndACaller, ProjectAdapter, Edited]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-edits-none-of-several-projects"

    @override
    def describe(self) -> str:
        return (
            "아무 권한도 받지 않은 사용자가 프로젝트 여럿을 한 번에 고치려 하면, 고쳐진 것 없이 "
            "모두 권한이 없다는 이유로 실패 목록에 온다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyProjectsAndACaller]:
        return ManyProjectsAndSomeone()

    @override
    def when(self) -> When[ManyProjectsAndACaller, ProjectAdapter, Edited]:
        return EditingEveryTarget()

    @override
    def then(self) -> Then[ManyProjectsAndACaller, Edited]:
        return NoProjectIsProcessed(reason="Insufficient permission")


SCENARIOS: list[ProjectStep] = [
    TheSuperadminEditsSeveralProjects(started=datetime.now(UTC)),
    AUserGrantedNothingEditsNone(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_partial_bulk_editing(
    scenario: ProjectStep, adapter: ProjectAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
