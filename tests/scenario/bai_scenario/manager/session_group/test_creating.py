"""세션 그룹 만들기 — 누가 어느 프로젝트에 세션 그룹을 만들 수 있는가.

세션 그룹 행과 그 그래프 노드가 생기고 프로젝트와 만든 사람 아래에 들어가는 것은 답에 나오지 않는다.
실행 뒤 데이터베이스에서 따로 확인한다.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override

import pytest
import sqlalchemy as sa

from ai.backend.common.data.entity.project import ProjectEntityType
from ai.backend.common.data.entity.session_group import SessionGroupEntityType
from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.entity.user import UserEntityType
from ai.backend.common.dto.manager.v2.session_group.request import CreateSessionGroupInput
from ai.backend.common.dto.manager.v2.session_group.response import SessionGroupNode
from ai.backend.common.dto.manager.v2.session_group.types import (
    SessionGroupPlacementDirectionEnum,
    SessionGroupPlacementEnforcementEnum,
)
from ai.backend.manager.api.adapters.session_group.adapter import SessionGroupAdapter
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.session_group.row import SessionGroupRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Scenario,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.answers import MissingResponse, TheCallIsRefused
from bai_scenario.components.session_group import (
    AProjectAndACaller,
    AProjectAndACallerGranted,
    CallerGrant,
    CreatedGroupLook,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Laid = AProjectAndACaller
type CreatingStep = Scenario[TestSeedingSession, Laid, SessionGroupAdapter, SessionGroupNode]

_SPREAD = SessionGroupPlacementDirectionEnum.SPREAD
_PREFERRED = SessionGroupPlacementEnforcementEnum.PREFERRED


@dataclass(frozen=True)
class CreatingInTheProject(When[Laid, SessionGroupAdapter, SessionGroupNode]):
    """세션 그룹을 만들 프로젝트에 세션 그룹을 만든다."""

    @override
    def operation(self) -> str:
        return "create"

    @override
    def describe(self, laid: Laid) -> str:
        return (
            f"{laid.caller.username}이 그 프로젝트에 방향은 퍼뜨리기, 강제 수준은 선호인 "
            "세션 그룹을 만든다"
        )

    @override
    async def call(self, adapter: SessionGroupAdapter, laid: Laid) -> SessionGroupNode:
        with ActingAs(laid.caller):
            payload = await adapter.create(
                CreateSessionGroupInput(
                    project_id=laid.project.id,
                    placement_direction=_SPREAD,
                    placement_enforcement=_PREFERRED,
                )
            )
        return payload.session_group


@dataclass(frozen=True)
class TheCreatedGroupNode(Then[Laid, SessionGroupNode]):
    """만든 사람이 소유자이고 입력한 배치 정책을 가진 세션 그룹의 노드가 통째로 온다."""

    started: datetime

    @override
    def says(self) -> str:
        return "만든 사람이 소유자이고 입력한 배치 정책을 가진 세션 그룹 전체가 온다"

    @override
    def look(self, laid: Laid, answered: Answered[SessionGroupNode]) -> list[Verdict]:
        node = answered.response
        if node is None:
            return [MissingResponse(answered.raised)]
        return CreatedGroupLook(self.started, direction=_SPREAD, enforcement=_PREFERRED).verdicts(
            node, laid
        )


@dataclass(frozen=True)
class AUserGrantedCreateCreates(
    Scenario[TestSeedingSession, Laid, SessionGroupAdapter, SessionGroupNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-create-in-a-project-creates-a-session-group-there"

    @override
    def describe(self) -> str:
        return (
            "프로젝트에서 세션 그룹 생성 권한을 받은 사용자가 그 프로젝트에 세션 그룹을 만들면, "
            "그 사용자가 소유자이고 입력한 배치 정책을 가진 세션 그룹이 온다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, Laid]:
        return AProjectAndACallerGranted(granted=CallerGrant.CREATE_IN_THE_PROJECT)

    @override
    def when(self) -> When[Laid, SessionGroupAdapter, SessionGroupNode]:
        return CreatingInTheProject()

    @override
    def then(self) -> Then[Laid, SessionGroupNode]:
        return TheCreatedGroupNode(started=self.started)


@dataclass(frozen=True)
class AReaderMayNotCreate(
    Scenario[TestSeedingSession, Laid, SessionGroupAdapter, SessionGroupNode]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-only-read-in-a-project-may-not-create-a-session-group"

    @override
    def describe(self) -> str:
        return (
            "프로젝트에서 세션 그룹 읽기 권한만 받은 사용자가 그 프로젝트에 세션 그룹을 만들면, "
            "권한 부족으로 거부되고 세션 그룹은 생기지 않는다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, Laid]:
        return AProjectAndACallerGranted(granted=CallerGrant.READ_IN_THE_PROJECT)

    @override
    def when(self) -> When[Laid, SessionGroupAdapter, SessionGroupNode]:
        return CreatingInTheProject()

    @override
    def then(self) -> Then[Laid, SessionGroupNode]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AnOutsiderMayNotCreate(
    Scenario[TestSeedingSession, Laid, SessionGroupAdapter, SessionGroupNode]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-create-only-in-another-project-may-not-create-a-session-group"

    @override
    def describe(self) -> str:
        return (
            "다른 프로젝트에서만 세션 그룹 생성 권한을 받은 사용자가 그 프로젝트에 세션 그룹을 "
            "만들면, 권한 부족으로 거부되고 세션 그룹은 생기지 않는다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, Laid]:
        return AProjectAndACallerGranted(granted=CallerGrant.CREATE_IN_THE_OTHER_PROJECT)

    @override
    def when(self) -> When[Laid, SessionGroupAdapter, SessionGroupNode]:
        return CreatingInTheProject()

    @override
    def then(self) -> Then[Laid, SessionGroupNode]:
        return TheCallIsRefused(NotEnoughPermission)


SCENARIOS: list[CreatingStep] = [
    AUserGrantedCreateCreates(started=datetime.now(UTC)),
    AReaderMayNotCreate(),
    AnOutsiderMayNotCreate(),
]


@dataclass(frozen=True)
class WhatIsLeft:
    """실행 뒤 데이터베이스에 남은 세션 그룹과 그 그래프 노드가 들어간 자리."""

    groups: int
    group_nodes: int
    under_a_project: int
    under_a_user: int


async def what_is_left(engine: ExtendedAsyncSAEngine) -> WhatIsLeft:
    parent = sa.orm.aliased(VirtualEntityRow)
    child = sa.orm.aliased(VirtualEntityRow)

    def held_by(entity_type: EntityType) -> sa.Select[tuple[int]]:
        return (
            sa.select(sa.func.count())
            .select_from(EntityMembershipRow)
            .join(parent, parent.id == EntityMembershipRow.virtual_entity_id)
            .join(child, child.id == EntityMembershipRow.member_entity_id)
            .where(
                child.entity_type == SessionGroupEntityType(),
                parent.entity_type == entity_type,
            )
        )

    async with engine.begin_readonly_session_read_committed() as sess:
        groups = await sess.scalar(sa.select(sa.func.count()).select_from(SessionGroupRow))
        group_nodes = await sess.scalar(
            sa.select(sa.func.count())
            .select_from(VirtualEntityRow)
            .where(VirtualEntityRow.entity_type == SessionGroupEntityType())
        )
        under_a_project = await sess.scalar(held_by(ProjectEntityType()))
        under_a_user = await sess.scalar(held_by(UserEntityType()))
    return WhatIsLeft(
        groups=groups or 0,
        group_nodes=group_nodes or 0,
        under_a_project=under_a_project or 0,
        under_a_user=under_a_user or 0,
    )


def expected_left(scenario: CreatingStep) -> WhatIsLeft:
    """만든 행만 세션 그룹 하나와 그 노드를 남기고, 그 노드는 프로젝트와 만든 사람 아래에 든다."""
    match scenario:
        case AUserGrantedCreateCreates():
            return WhatIsLeft(groups=1, group_nodes=1, under_a_project=1, under_a_user=1)
        case _:
            return WhatIsLeft(groups=0, group_nodes=0, under_a_project=0, under_a_user=0)


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_creating(
    scenario: CreatingStep, adapter: SessionGroupAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
    assert await what_is_left(engine) == expected_left(scenario)
