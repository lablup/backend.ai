"""프로젝트 여럿 수정하기."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override
from uuid import UUID

import pytest

from ai.backend.common.data.entity.project import ProjectID
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
    Held,
    Refused,
    Same,
    SameAs,
    Scenario,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.domain import Mentions
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
class FlippingTheActiveFlagOfEach(When[ManyProjectsAndACaller, ProjectAdapter, Edited]):
    """둘째 대상을 soft delete 한 뒤, 활성 플래그와 설명을 섞어 한 번에 고친다.

    첫째는 플래그를 내리고, 둘째는 올리고, `missing`은 플래그를 내린다.
    """

    missing: UUID

    @override
    def operation(self) -> str:
        return "partial_bulk_update"

    @override
    def describe(self, laid: ManyProjectsAndACaller) -> str:
        return (
            f"{laid.caller.username}이 둘째 프로젝트를 soft delete 한 뒤, 첫째는 활성 플래그를 "
            "내리고 둘째는 올리며 둘의 설명을 바꾸고, 없는 id 하나의 활성 플래그를 내림"
        )

    @override
    async def call(self, adapter: ProjectAdapter, laid: ManyProjectsAndACaller) -> Edited:
        first, second = laid.targets
        with ActingAs(laid.caller):
            await adapter.delete(ProjectID(second.id))
            return await adapter.partial_bulk_update(
                PartialBulkUpdateProjectsInput(
                    items=[
                        PartialBulkUpdateProjectItemInput(
                            id=first.id,
                            input=UpdateProjectInput(is_active=False, description=EDITED),
                        ),
                        PartialBulkUpdateProjectItemInput(
                            id=second.id,
                            input=UpdateProjectInput(is_active=True, description=EDITED),
                        ),
                        PartialBulkUpdateProjectItemInput(
                            id=self.missing, input=UpdateProjectInput(is_active=False)
                        ),
                    ]
                )
            )


@dataclass(frozen=True)
class EachFlagIsFlipped(Then[ManyProjectsAndACaller, Edited]):
    """둘 다 새 설명으로 오고 첫째는 비활성, 둘째는 활성이다. `missing`만 실패 목록에 온다."""

    started: datetime
    missing: UUID

    @override
    def says(self) -> str:
        return (
            "둘 다 새 설명으로 오고 첫째는 비활성, 둘째는 활성이며, 없는 id 는 대상이 없다는 "
            "이유로 실패 목록에 온다"
        )

    @override
    def look(self, laid: ManyProjectsAndACaller, answered: Answered[Edited]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        first, second = laid.targets
        verdicts: list[Verdict] = [Same("successes count", len(payload.successes), 2)]
        looks = [
            (ProjectLook(self.started, described=EDITED, active=False), first),
            (ProjectLook(self.started, described=EDITED, active=True), second),
        ]
        for i, (node, (look, project)) in enumerate(zip(payload.successes, looks, strict=False)):
            verdicts += look.verdicts(f"successes[{i}].", node, project)
        verdicts.append(Same("failed count", len(payload.failed), 1))
        for failure in payload.failed:
            verdicts += [
                Held[UUID]("failed[0].id", failure.id, SameAs(self.missing, "요청에 넣은 없는 id")),
                Held("failed[0].message", failure.message, Mentions("not found")),
            ]
        return verdicts


@dataclass(frozen=True)
class TheActiveFlagSoftDeletesOrRestoresEach(
    Scenario[TestSeedingSession, ManyProjectsAndACaller, ProjectAdapter, Edited]
):
    started: datetime
    missing: UUID = UUID(int=1)

    @override
    def summary(self) -> str:
        return "the-active-flag-soft-deletes-or-restores-each-of-several-projects"

    @override
    def describe(self) -> str:
        return (
            "활성 플래그와 설명을 섞어 프로젝트 여럿을 한 번에 고치면, 플래그를 내린 것은 soft "
            "delete 되고 올린 것은 restore 되며 둘 다 새 설명으로 오고, 없는 id 는 대상이 "
            "없다는 이유로 실패 목록에 온다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyProjectsAndACaller]:
        return ManyProjectsAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyProjectsAndACaller, ProjectAdapter, Edited]:
        return FlippingTheActiveFlagOfEach(missing=self.missing)

    @override
    def then(self) -> Then[ManyProjectsAndACaller, Edited]:
        return EachFlagIsFlipped(started=self.started, missing=self.missing)


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
    TheActiveFlagSoftDeletesOrRestoresEach(started=datetime.now(UTC)),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_partial_bulk_editing(
    scenario: ProjectStep, adapter: ProjectAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
