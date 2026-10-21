"""세션 그룹 배치 정책 바꾸기 — 누가 어느 세션 그룹의 정책을 바꿀 수 있는가."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override

import pytest

from ai.backend.common.dto.manager.v2.session_group.request import UpdateSessionGroupInput
from ai.backend.common.dto.manager.v2.session_group.response import SessionGroupNode
from ai.backend.common.dto.manager.v2.session_group.types import (
    SessionGroupPlacementDirectionEnum,
    SessionGroupPlacementEnforcementEnum,
)
from ai.backend.common.tristate.unset import UNSET, Unset
from ai.backend.manager.api.adapters.session_group.adapter import SessionGroupAdapter
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.errors.session_group import SessionGroupInUseForUpdate
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
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
    GrantedIn,
    Granting,
    SessionGroupsAndACaller,
    SessionGroupsInTwoProjects,
    UsersGroupLook,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Laid = SessionGroupsAndACaller
type UpdatingStep = Scenario[TestSeedingSession, Laid, SessionGroupAdapter, SessionGroupNode]

_SPREAD = SessionGroupPlacementDirectionEnum.SPREAD
_PREFERRED = SessionGroupPlacementEnforcementEnum.PREFERRED


@dataclass(frozen=True)
class UpdatingTheUsersGroup(When[Laid, SessionGroupAdapter, SessionGroupNode]):
    """사용자가 만든 세션 그룹의 배치 정책을 바꾼다. 빠진 항목은 그대로 둔다."""

    enforcement: SessionGroupPlacementEnforcementEnum | Unset = _PREFERRED

    @override
    def operation(self) -> str:
        return "update"

    @override
    def describe(self, laid: Laid) -> str:
        if isinstance(self.enforcement, Unset):
            return f"{laid.caller.username}이 사용자가 만든 세션 그룹의 방향만 퍼뜨리기로 바꾼다"
        return (
            f"{laid.caller.username}이 사용자가 만든 세션 그룹의 방향을 퍼뜨리기로, "
            "강제 수준을 선호로 바꾼다"
        )

    @override
    async def call(self, adapter: SessionGroupAdapter, laid: Laid) -> SessionGroupNode:
        with ActingAs(laid.caller):
            payload = await adapter.update(
                UpdateSessionGroupInput(
                    id=laid.users_group.id,
                    placement_direction=_SPREAD,
                    placement_enforcement=self.enforcement,
                )
            )
        return payload.session_group


@dataclass(frozen=True)
class UpdatingTheDeploymentGroup(When[Laid, SessionGroupAdapter, SessionGroupNode]):
    """배포의 replica group이 가진 세션 그룹의 배치 정책을 바꾼다."""

    @override
    def operation(self) -> str:
        return "update"

    @override
    def describe(self, laid: Laid) -> str:
        return (
            f"{laid.caller.username}이 배포의 replica group이 가진 세션 그룹의 방향을 퍼뜨리기로, "
            "강제 수준을 선호로 바꾼다"
        )

    @override
    async def call(self, adapter: SessionGroupAdapter, laid: Laid) -> SessionGroupNode:
        with ActingAs(laid.caller):
            payload = await adapter.update(
                UpdateSessionGroupInput(
                    id=laid.deployment_group.id,
                    placement_direction=_SPREAD,
                    placement_enforcement=_PREFERRED,
                )
            )
        return payload.session_group


@dataclass(frozen=True)
class TheUpdatedGroupNode(Then[Laid, SessionGroupNode]):
    """정책이 바뀐, 사용자가 만든 세션 그룹의 노드가 통째로 온다."""

    started: datetime
    enforcement: SessionGroupPlacementEnforcementEnum
    said: str

    @override
    def says(self) -> str:
        return self.said

    @override
    def look(self, laid: Laid, answered: Answered[SessionGroupNode]) -> list[Verdict]:
        node = answered.response
        if node is None:
            return [MissingResponse(answered.raised)]
        return UsersGroupLook(
            self.started, direction=_SPREAD, enforcement=self.enforcement
        ).verdicts("", node, laid)


@dataclass(frozen=True)
class AnOwnerChangesBothItems(
    Scenario[TestSeedingSession, SessionGroupsAndACaller, SessionGroupAdapter, SessionGroupNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "an-owner-changes-the-direction-and-the-enforcement"

    @override
    def describe(self) -> str:
        return (
            "자기 스코프에서 세션 그룹 수정 권한을 받은 사용자가 자기가 만든 세션 그룹의 방향과 "
            "강제 수준을 바꾸면, 두 항목이 바뀐 그 세션 그룹이 온다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, Laid]:
        return SessionGroupsInTwoProjects(granted_in=GrantedIn.THEIR_OWN, granting=Granting.UPDATE)

    @override
    def when(self) -> When[Laid, SessionGroupAdapter, SessionGroupNode]:
        return UpdatingTheUsersGroup()

    @override
    def then(self) -> Then[Laid, SessionGroupNode]:
        return TheUpdatedGroupNode(
            started=self.started,
            enforcement=_PREFERRED,
            said="두 항목이 바뀐 세션 그룹 전체가 온다",
        )


@dataclass(frozen=True)
class AnOwnerChangesOnlyTheDirection(
    Scenario[TestSeedingSession, SessionGroupsAndACaller, SessionGroupAdapter, SessionGroupNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "an-owner-changes-only-the-direction"

    @override
    def describe(self) -> str:
        return (
            "자기 스코프에서 세션 그룹 수정 권한을 받은 사용자가 자기가 만든 세션 그룹의 방향만 "
            "바꾸면, 강제 수준은 그대로인 그 세션 그룹이 온다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, Laid]:
        return SessionGroupsInTwoProjects(granted_in=GrantedIn.THEIR_OWN, granting=Granting.UPDATE)

    @override
    def when(self) -> When[Laid, SessionGroupAdapter, SessionGroupNode]:
        return UpdatingTheUsersGroup(enforcement=UNSET)

    @override
    def then(self) -> Then[Laid, SessionGroupNode]:
        return TheUpdatedGroupNode(
            started=self.started,
            enforcement=SessionGroupPlacementEnforcementEnum.STRICT,
            said="방향만 바뀌고 강제 수준은 그대로인 세션 그룹 전체가 온다",
        )


@dataclass(frozen=True)
class AnOwnerGrantedOnlyReadMayNotUpdate(
    Scenario[TestSeedingSession, SessionGroupsAndACaller, SessionGroupAdapter, SessionGroupNode]
):
    @override
    def summary(self) -> str:
        return "an-owner-granted-only-read-may-not-update"

    @override
    def describe(self) -> str:
        return (
            "자기 스코프에서 세션 그룹 읽기 권한만 받은 사용자가 자기가 만든 세션 그룹의 정책을 "
            "바꾸면, 권한 부족으로 거부된다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, Laid]:
        return SessionGroupsInTwoProjects(granted_in=GrantedIn.THEIR_OWN, granting=Granting.READ)

    @override
    def when(self) -> When[Laid, SessionGroupAdapter, SessionGroupNode]:
        return UpdatingTheUsersGroup()

    @override
    def then(self) -> Then[Laid, SessionGroupNode]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class ADeploymentsGroupIsRefusedAsInUse(
    Scenario[TestSeedingSession, SessionGroupsAndACaller, SessionGroupAdapter, SessionGroupNode]
):
    @override
    def summary(self) -> str:
        return "a-deployments-session-group-is-refused-as-in-use"

    @override
    def describe(self) -> str:
        return (
            "자기 스코프에서 세션 그룹 수정 권한을 받은 사용자가 자기 배포의 replica group이 가진 세션 그룹 정책을 "
            "바꾸면, 권한이 아니라 사용 중이라는 것으로 거부된다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, Laid]:
        return SessionGroupsInTwoProjects(granted_in=GrantedIn.THEIR_OWN, granting=Granting.UPDATE)

    @override
    def when(self) -> When[Laid, SessionGroupAdapter, SessionGroupNode]:
        return UpdatingTheDeploymentGroup()

    @override
    def then(self) -> Then[Laid, SessionGroupNode]:
        return TheCallIsRefused(SessionGroupInUseForUpdate)


SCENARIOS: list[UpdatingStep] = [
    AnOwnerChangesBothItems(started=datetime.now(UTC)),
    AnOwnerChangesOnlyTheDirection(started=datetime.now(UTC)),
    AnOwnerGrantedOnlyReadMayNotUpdate(),
    ADeploymentsGroupIsRefusedAsInUse(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_updating(
    scenario: UpdatingStep, adapter: SessionGroupAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
