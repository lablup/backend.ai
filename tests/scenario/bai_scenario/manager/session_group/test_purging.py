"""세션 그룹 영구 삭제 — 누가 지울 수 있고, 지운 뒤 무엇이 남는가.

세션 그룹 행과 그 그래프 노드가 사라지고 멤버 세션은 세션 그룹 id가 비워진 채 남는 것은 답에 나오지
않는다. 실행 뒤 데이터베이스에서 따로 확인한다.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import override
from uuid import UUID

import pytest
import sqlalchemy as sa

from ai.backend.common.data.entity.session_group import SessionGroupEntityType
from ai.backend.common.dto.manager.v2.session_group.request import PurgeSessionGroupInput
from ai.backend.common.dto.manager.v2.session_group.response import PurgeSessionGroupPayload
from ai.backend.manager.api.adapters.session_group.adapter import SessionGroupAdapter
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.errors.session_group import SessionGroupInUse
from ai.backend.manager.models.session.row import SessionRow
from ai.backend.manager.models.session_group.row import SessionGroupRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    Refused,
    SameAs,
    Scenario,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.session_group import (
    AGroupWithMembersAndItsOwner,
    AUsersGroupWithMembers,
    OwnerGrant,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Laid = AGroupWithMembersAndItsOwner
type PurgingStep = Scenario[TestSeedingSession, Laid, SessionGroupAdapter, PurgeSessionGroupPayload]


@dataclass(frozen=True)
class PurgingTheUsersGroup(When[Laid, SessionGroupAdapter, PurgeSessionGroupPayload]):
    """사용자가 만든 세션 그룹을 영구 삭제한다."""

    @override
    def operation(self) -> str:
        return "purge"

    @override
    def describe(self, laid: Laid) -> str:
        return f"{laid.owner.username}이 사용자가 만든 세션 그룹을 영구 삭제"

    @override
    async def call(self, adapter: SessionGroupAdapter, laid: Laid) -> PurgeSessionGroupPayload:
        with ActingAs(laid.owner):
            return await adapter.purge(PurgeSessionGroupInput(id=laid.users_group.id))


@dataclass(frozen=True)
class PurgingTheDeploymentGroup(When[Laid, SessionGroupAdapter, PurgeSessionGroupPayload]):
    """배포의 replica group이 가진 세션 그룹을 영구 삭제한다."""

    @override
    def operation(self) -> str:
        return "purge"

    @override
    def describe(self, laid: Laid) -> str:
        return f"{laid.owner.username}이 배포의 replica group이 가진 세션 그룹을 영구 삭제"

    @override
    async def call(self, adapter: SessionGroupAdapter, laid: Laid) -> PurgeSessionGroupPayload:
        with ActingAs(laid.owner):
            return await adapter.purge(PurgeSessionGroupInput(id=laid.deployment_group.id))


@dataclass(frozen=True)
class TheUsersGroupIsNamed(Then[Laid, PurgeSessionGroupPayload]):
    """지운 세션 그룹의 id가 온다."""

    @override
    def says(self) -> str:
        return "지운 사용자가 만든 세션 그룹의 id가 온다"

    @override
    def look(self, laid: Laid, answered: Answered[PurgeSessionGroupPayload]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        return [
            Held[UUID](
                "id", payload.id, SameAs(laid.users_group.id, "사용자가 만든 세션 그룹의 id")
            )
        ]


@dataclass(frozen=True)
class TheOwnerPurgesTheUsersGroup(
    Scenario[TestSeedingSession, Laid, SessionGroupAdapter, PurgeSessionGroupPayload]
):
    @override
    def summary(self) -> str:
        return "the-owner-purges-a-users-session-group-keeping-its-members"

    @override
    def describe(self) -> str:
        return (
            "자기 스코프에서 세션 그룹 영구 삭제 권한을 받은 사용자가 자기가 만든 세션 그룹을 지우면, "
            "그 세션 그룹의 id가 오고 멤버 세션은 세션 그룹이 비워진 채 남는다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, Laid]:
        return AUsersGroupWithMembers(granted=OwnerGrant.HARD_DELETE)

    @override
    def when(self) -> When[Laid, SessionGroupAdapter, PurgeSessionGroupPayload]:
        return PurgingTheUsersGroup()

    @override
    def then(self) -> Then[Laid, PurgeSessionGroupPayload]:
        return TheUsersGroupIsNamed()


@dataclass(frozen=True)
class ADeploymentsGroupIsInUse(
    Scenario[TestSeedingSession, Laid, SessionGroupAdapter, PurgeSessionGroupPayload]
):
    @override
    def summary(self) -> str:
        return "a-deployments-session-group-is-refused-as-in-use"

    @override
    def describe(self) -> str:
        return (
            "자기 스코프에서 세션 그룹 영구 삭제 권한을 받은 사용자가 배포의 replica group이 가진 세션 그룹을 지우면, "
            "replica group이 사용 중이라는 것으로 거부되고 세션 그룹은 남는다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, Laid]:
        return AUsersGroupWithMembers(granted=OwnerGrant.HARD_DELETE)

    @override
    def when(self) -> When[Laid, SessionGroupAdapter, PurgeSessionGroupPayload]:
        return PurgingTheDeploymentGroup()

    @override
    def then(self) -> Then[Laid, PurgeSessionGroupPayload]:
        return TheCallIsRefused(SessionGroupInUse)


@dataclass(frozen=True)
class AReaderMayNotPurge(
    Scenario[TestSeedingSession, Laid, SessionGroupAdapter, PurgeSessionGroupPayload]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-only-read-may-not-purge-a-session-group"

    @override
    def describe(self) -> str:
        return (
            "자기 스코프에서 세션 그룹 읽기 권한만 받은 사용자가 자기가 만든 세션 그룹을 지우면, "
            "권한 부족으로 거부되고 세션 그룹은 남는다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, Laid]:
        return AUsersGroupWithMembers(granted=OwnerGrant.READ)

    @override
    def when(self) -> When[Laid, SessionGroupAdapter, PurgeSessionGroupPayload]:
        return PurgingTheUsersGroup()

    @override
    def then(self) -> Then[Laid, PurgeSessionGroupPayload]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotPurge(
    Scenario[TestSeedingSession, Laid, SessionGroupAdapter, PurgeSessionGroupPayload]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-purge-a-session-group"

    @override
    def describe(self) -> str:
        return (
            "아무 권한도 받지 않은 사용자가 자기가 만든 세션 그룹을 지우면, 권한 부족으로 거부되고 "
            "세션 그룹은 남는다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, Laid]:
        return AUsersGroupWithMembers(granted=OwnerGrant.NOTHING)

    @override
    def when(self) -> When[Laid, SessionGroupAdapter, PurgeSessionGroupPayload]:
        return PurgingTheUsersGroup()

    @override
    def then(self) -> Then[Laid, PurgeSessionGroupPayload]:
        return TheCallIsRefused(NotEnoughPermission)


SCENARIOS: list[PurgingStep] = [
    TheOwnerPurgesTheUsersGroup(),
    ADeploymentsGroupIsInUse(),
    AReaderMayNotPurge(),
    AUserGrantedNothingMayNotPurge(),
]


@dataclass(frozen=True)
class WhatIsLeft:
    """실행 뒤 데이터베이스에 남은 세션 그룹과 그 멤버."""

    groups: int
    group_nodes: int
    members_in_a_group: int
    members_without_a_group: int


async def what_is_left(engine: ExtendedAsyncSAEngine) -> WhatIsLeft:
    async with engine.begin_readonly_session_read_committed() as sess:
        groups = await sess.scalar(sa.select(sa.func.count()).select_from(SessionGroupRow))
        group_nodes = await sess.scalar(
            sa.select(sa.func.count())
            .select_from(VirtualEntityRow)
            .where(VirtualEntityRow.entity_type == SessionGroupEntityType())
        )
        in_a_group = await sess.scalar(
            sa.select(sa.func.count())
            .select_from(SessionRow)
            .where(SessionRow.session_group_id.is_not(None))
        )
        without_a_group = await sess.scalar(
            sa.select(sa.func.count())
            .select_from(SessionRow)
            .where(SessionRow.session_group_id.is_(None))
        )
    return WhatIsLeft(
        groups=groups or 0,
        group_nodes=group_nodes or 0,
        members_in_a_group=in_a_group or 0,
        members_without_a_group=without_a_group or 0,
    )


def expected_left(scenario: PurgingStep) -> WhatIsLeft:
    """사용자가 만든 세션 그룹을 지운 행만 세션 그룹 하나와 그 노드를 잃고, 멤버 둘은 세션 그룹 없이 남는다."""
    match scenario:
        case TheOwnerPurgesTheUsersGroup():
            return WhatIsLeft(
                groups=1, group_nodes=1, members_in_a_group=0, members_without_a_group=2
            )
        case _:
            return WhatIsLeft(
                groups=2, group_nodes=2, members_in_a_group=2, members_without_a_group=0
            )


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_purging(
    scenario: PurgingStep, adapter: SessionGroupAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
    assert await what_is_left(engine) == expected_left(scenario)
