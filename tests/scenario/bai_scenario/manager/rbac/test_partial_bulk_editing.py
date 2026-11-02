"""역할 여럿 수정하기."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override

import pytest

from ai.backend.common.data.permission.types import RoleStatus
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.common import PartialBulkPayload
from ai.backend.common.dto.manager.v2.rbac.request import (
    PartialBulkDeleteRolesInput,
    PartialBulkUpdateRoleItemInput,
    PartialBulkUpdateRolesInput,
    UpdateRoleInput,
)
from ai.backend.common.dto.manager.v2.rbac.response import RoleNode
from ai.backend.common.dto.manager.v2.rbac.types import RoleStatusDTO
from ai.backend.manager.api.adapters.rbac.adapter import RBACAdapter
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Refused,
    Same,
    Says,
    Scenario,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.rbac import (
    NothingIsProcessed,
    RoleLook,
    RolesAndACaller,
    RolesAndSomeone,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

EDITED = Says("한 번에 수정한 설명", english="the description edited in one call")

type Edited = PartialBulkPayload[RoleNode]
type RoleStep = Scenario[TestSeedingSession, RolesAndACaller, RBACAdapter, Edited]


@dataclass(frozen=True)
class EditingEveryRole(When[RolesAndACaller, RBACAdapter, Edited]):
    """역할들의 설명을 한 번에 고친다."""

    @override
    def operation(self) -> str:
        return "partial_bulk_update"

    @override
    def describe(self, laid: RolesAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 역할 {len(laid.roles)}개의 설명을 한 번에 수정합니다",
            english=(
                f"{laid.caller.username} edits the description of {len(laid.roles)} roles in "
                "one call"
            ),
        )

    @override
    async def call(self, adapter: RBACAdapter, laid: RolesAndACaller) -> Edited:
        with ActingAs(laid.caller):
            return await adapter.partial_bulk_update(
                PartialBulkUpdateRolesInput(
                    items=[
                        PartialBulkUpdateRoleItemInput(
                            id=role.id, input=UpdateRoleInput(description=EDITED)
                        )
                        for role in laid.roles
                    ]
                )
            )


@dataclass(frozen=True)
class SoftDeletingThenEditingStatusToActive(When[RolesAndACaller, RBACAdapter, Edited]):
    """역할들을 한 번에 soft delete 했다가 status 를 ACTIVE 로 한 번에 고친다."""

    @override
    def operation(self) -> str:
        return "partial_bulk_update"

    @override
    def describe(self, laid: RolesAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 역할 {len(laid.roles)}개를 한 번에 soft delete 했다가 "
            "status 를 ACTIVE 로 한 번에 변경합니다",
            english=(
                f"{laid.caller.username} soft deletes {len(laid.roles)} roles in one call and "
                "then changes their status to ACTIVE in one call"
            ),
        )

    @override
    async def call(self, adapter: RBACAdapter, laid: RolesAndACaller) -> Edited:
        with ActingAs(laid.caller):
            await adapter.partial_bulk_delete(
                PartialBulkDeleteRolesInput(ids=[role.id for role in laid.roles])
            )
            return await adapter.partial_bulk_update(
                PartialBulkUpdateRolesInput(
                    items=[
                        PartialBulkUpdateRoleItemInput(
                            id=role.id, input=UpdateRoleInput(status=RoleStatus.ACTIVE)
                        )
                        for role in laid.roles
                    ]
                )
            )


@dataclass(frozen=True)
class EveryRoleIsRestored(Then[RolesAndACaller, Edited]):
    """역할이 모두 활성으로 처리된 목록에 오고, 실패 목록은 비어 있다."""

    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "역할이 모두 활성으로 오고, 실패한 것은 없습니다",
            english="every role comes back active and nothing failed",
        )

    @override
    def look(self, laid: RolesAndACaller, answered: Answered[Edited]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        look = RoleLook(self.started, status=RoleStatusDTO.ACTIVE)
        verdicts: list[Verdict] = [
            Same("successes count", len(payload.successes), len(laid.roles)),
            Same("failed", payload.failed, []),
        ]
        for i, (node, role) in enumerate(zip(payload.successes, laid.roles, strict=False)):
            verdicts += look.verdicts(f"successes[{i}].", node, role, laid.domain)
        return verdicts


@dataclass(frozen=True)
class EveryRoleIsEdited(Then[RolesAndACaller, Edited]):
    """역할이 모두 새 설명을 싣고 처리된 목록에 오고, 실패 목록은 비어 있다."""

    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "역할이 모두 새 설명으로 오고, 실패한 것은 없습니다",
            english="every role comes back with the new description and nothing failed",
        )

    @override
    def look(self, laid: RolesAndACaller, answered: Answered[Edited]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        look = RoleLook(self.started, described=EDITED)
        verdicts: list[Verdict] = [
            Same("successes count", len(payload.successes), len(laid.roles)),
            Same("failed", payload.failed, []),
        ]
        for i, (node, role) in enumerate(zip(payload.successes, laid.roles, strict=False)):
            verdicts += look.verdicts(f"successes[{i}].", node, role, laid.domain)
        return verdicts


@dataclass(frozen=True)
class TheSuperadminEditsSeveralRoles(
    Scenario[TestSeedingSession, RolesAndACaller, RBACAdapter, Edited]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-edits-several-roles-at-once"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 역할 여럿의 설명을 한 번에 변경하면, 모두 새 설명으로 오고 실패한 "
            "것은 없습니다",
            english=(
                "when the superadmin changes the description of several roles in one call, all "
                "come back with the new description and nothing failed"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, RolesAndACaller]:
        return RolesAndSomeone(role=UserRole.SUPERADMIN, count=2)

    @override
    def when(self) -> When[RolesAndACaller, RBACAdapter, Edited]:
        return EditingEveryRole()

    @override
    def then(self) -> Then[RolesAndACaller, Edited]:
        return EveryRoleIsEdited(started=self.started)


@dataclass(frozen=True)
class AUserGrantedNothingEditsNone(
    Scenario[TestSeedingSession, RolesAndACaller, RBACAdapter, Edited]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-edits-none-of-several-roles"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 역할 여럿을 한 번에 수정하려 하면, 수정된 것 없이 "
            "모두 권한이 없다는 이유로 실패 목록에 옵니다",
            english=(
                "when a user granted nothing tries to edit several roles in one call, none is "
                "edited and all come back in the failed list for lack of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, RolesAndACaller]:
        return RolesAndSomeone(count=2)

    @override
    def when(self) -> When[RolesAndACaller, RBACAdapter, Edited]:
        return EditingEveryRole()

    @override
    def then(self) -> Then[RolesAndACaller, Edited]:
        return NothingIsProcessed(reason="Insufficient permission")


@dataclass(frozen=True)
class EditingStatusToActiveRestoresSeveral(
    Scenario[TestSeedingSession, RolesAndACaller, RBACAdapter, Edited]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "editing-status-to-active-restores-several-roles"

    @override
    def describe(self) -> str:
        return Says(
            "soft delete 된 역할 여럿의 status 를 한 번에 ACTIVE 로 변경하면, restore 되어 "
            "모두 활성으로 옵니다",
            english=(
                "when the status of several soft-deleted roles is changed to ACTIVE in one "
                "call, they are restored and all come back active"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, RolesAndACaller]:
        return RolesAndSomeone(role=UserRole.SUPERADMIN, count=2)

    @override
    def when(self) -> When[RolesAndACaller, RBACAdapter, Edited]:
        return SoftDeletingThenEditingStatusToActive()

    @override
    def then(self) -> Then[RolesAndACaller, Edited]:
        return EveryRoleIsRestored(started=self.started)


SCENARIOS: list[RoleStep] = [
    TheSuperadminEditsSeveralRoles(started=datetime.now(UTC)),
    EditingStatusToActiveRestoresSeveral(started=datetime.now(UTC)),
    AUserGrantedNothingEditsNone(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_partial_bulk_editing(
    scenario: RoleStep, adapter: RBACAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
