"""역할 수정."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override

import pytest

from ai.backend.common.data.entity.role import RoleEntityType
from ai.backend.common.data.permission.types import RoleStatus
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.rbac.request import UpdateRoleInput
from ai.backend.common.dto.manager.v2.rbac.response import RoleNode
from ai.backend.common.dto.manager.v2.rbac.types import RoleStatusDTO
from ai.backend.manager.api.adapters.rbac.adapter import RBACAdapter
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Refused,
    Says,
    Scenario,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.domain import TheCallIsRefused
from bai_scenario.components.rbac import (
    Granted,
    RoleLook,
    RolesAndACaller,
    RolesAndSomeone,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

EDITED = Says("수정한 설명", english="the edited description")

type RoleStep = Scenario[TestSeedingSession, RolesAndACaller, RBACAdapter, RoleNode]


@dataclass(frozen=True)
class Editing(When[RolesAndACaller, RBACAdapter, RoleNode]):
    """역할의 설명을 고친다."""

    @override
    def operation(self) -> str:
        return "update"

    @override
    def describe(self, laid: RolesAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.role.name} 의 설명을 수정합니다",
            english=f"{laid.caller.username} edits the description of {laid.role.name}",
        )

    @override
    async def call(self, adapter: RBACAdapter, laid: RolesAndACaller) -> RoleNode:
        with ActingAs(laid.caller):
            payload = await adapter.update(laid.role.id, UpdateRoleInput(description=EDITED))
        return payload.role


@dataclass(frozen=True)
class EditingStatusToDeleted(When[RolesAndACaller, RBACAdapter, RoleNode]):
    """역할의 deprecated status 를 DELETED 로 고친다."""

    @override
    def operation(self) -> str:
        return "update"

    @override
    def describe(self, laid: RolesAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.role.name} 의 status 를 DELETED 로 변경합니다",
            english=f"{laid.caller.username} changes the status of {laid.role.name} to DELETED",
        )

    @override
    async def call(self, adapter: RBACAdapter, laid: RolesAndACaller) -> RoleNode:
        with ActingAs(laid.caller):
            payload = await adapter.update(laid.role.id, UpdateRoleInput(status=RoleStatus.DELETED))
        return payload.role


@dataclass(frozen=True)
class TheSoftDeletedRole(Then[RolesAndACaller, RoleNode]):
    """삭제 상태의 역할 전체가 온다."""

    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "삭제 상태의 역할 전체가 응답으로 옵니다",
            english="the whole role in the deleted state comes back",
        )

    @override
    def look(self, laid: RolesAndACaller, answered: Answered[RoleNode]) -> list[Verdict]:
        node = answered.response
        if node is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        return RoleLook(self.started, status=RoleStatusDTO.DELETED).verdicts(
            "", node, laid.role, laid.domain.id
        )


@dataclass(frozen=True)
class TheEditedRole(Then[RolesAndACaller, RoleNode]):
    """새 설명을 실은 역할 전체가 온다."""

    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "새 설명을 담은 역할 전체가 응답으로 옵니다",
            english="the whole role carrying the new description comes back",
        )

    @override
    def look(self, laid: RolesAndACaller, answered: Answered[RoleNode]) -> list[Verdict]:
        node = answered.response
        if node is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        return RoleLook(self.started, described=EDITED).verdicts(
            "", node, laid.role, laid.domain.id
        )


@dataclass(frozen=True)
class TheSuperadminEditsARole(Scenario[TestSeedingSession, RolesAndACaller, RBACAdapter, RoleNode]):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-edits-a-role"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 역할의 설명을 변경하면, 새 설명을 담은 역할 전체가 응답으로 옵니다",
            english=(
                "when the superadmin changes the description of a role, the whole role carrying "
                "the new description comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, RolesAndACaller]:
        return RolesAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[RolesAndACaller, RBACAdapter, RoleNode]:
        return Editing()

    @override
    def then(self) -> Then[RolesAndACaller, RoleNode]:
        return TheEditedRole(started=self.started)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotEdit(
    Scenario[TestSeedingSession, RolesAndACaller, RBACAdapter, RoleNode]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-edit-a-role"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자는 역할을 수정할 수 없습니다",
            english="a user granted nothing cannot edit a role",
        )

    @override
    def given(self) -> Given[TestSeedingSession, RolesAndACaller]:
        return RolesAndSomeone()

    @override
    def when(self) -> When[RolesAndACaller, RBACAdapter, RoleNode]:
        return Editing()

    @override
    def then(self) -> Then[RolesAndACaller, RoleNode]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AUserGrantedReadOnlyMayNotEdit(
    Scenario[TestSeedingSession, RolesAndACaller, RBACAdapter, RoleNode]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-read-only-may-not-edit-a-role"

    @override
    def describe(self) -> str:
        return Says(
            "대상 도메인에서 역할 조회 권한만 받은 사용자는 역할을 수정할 수 없습니다",
            english=("a user granted only role read permission in a domain cannot edit a role"),
        )

    @override
    def given(self) -> Given[TestSeedingSession, RolesAndACaller]:
        return RolesAndSomeone(grant=(Granted(RoleEntityType(), Permission.READ),))

    @override
    def when(self) -> When[RolesAndACaller, RBACAdapter, RoleNode]:
        return Editing()

    @override
    def then(self) -> Then[RolesAndACaller, RoleNode]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class EditingStatusToDeletedSoftDeletes(
    Scenario[TestSeedingSession, RolesAndACaller, RBACAdapter, RoleNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "editing-status-to-deleted-soft-deletes-the-role"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 역할의 status 를 DELETED 로 변경하면, soft delete 되어 삭제 상태로 "
            "옵니다",
            english=(
                "when the superadmin changes the status of a role to DELETED, it is soft "
                "deleted and comes back in the deleted state"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, RolesAndACaller]:
        return RolesAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[RolesAndACaller, RBACAdapter, RoleNode]:
        return EditingStatusToDeleted()

    @override
    def then(self) -> Then[RolesAndACaller, RoleNode]:
        return TheSoftDeletedRole(started=self.started)


SCENARIOS: list[RoleStep] = [
    TheSuperadminEditsARole(started=datetime.now(UTC)),
    EditingStatusToDeletedSoftDeletes(started=datetime.now(UTC)),
    AUserGrantedNothingMayNotEdit(),
    AUserGrantedReadOnlyMayNotEdit(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_editing(
    scenario: RoleStep, adapter: RBACAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
