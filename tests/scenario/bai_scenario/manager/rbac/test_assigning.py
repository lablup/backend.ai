"""역할 배정 — 주기, 회수, 여럿에게 주기, 여럿에게서 회수."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, override
from uuid import UUID

import pytest

from ai.backend.common.data.entity.role import RoleEntityType, RoleID
from ai.backend.common.data.entity.user import UserEntityType, UserID
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.dto.manager.v2.rbac.request import (
    AssignRoleInput,
    BulkAssignRoleInput,
    BulkRevokeRoleInput,
    RevokeRoleInput,
)
from ai.backend.common.dto.manager.v2.rbac.response import (
    BulkAssignRoleResultPayload,
    BulkRevokeRoleResultPayload,
    RoleAssignmentNode,
)
from ai.backend.manager.api.adapters.rbac.adapter import RBACAdapter
from ai.backend.manager.errors.permission import (
    NotEnoughPermission,
    RoleAlreadyAssigned,
    RoleNotAssigned,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    Refused,
    Same,
    SameAs,
    Says,
    Scenario,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.domain import Mentions, TheCallIsRefused
from bai_scenario.components.rbac import (
    AssignmentLook,
    Granted,
    RolesAndACaller,
    RolesAndSomeone,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type AssignmentStep = Scenario[TestSeedingSession, RolesAndACaller, RBACAdapter, Any]

GRANTING = (
    Granted(RoleEntityType(), Permission.CREATE),
    Granted(UserEntityType(), Permission.CREATE),
)
REVOKING = (
    Granted(RoleEntityType(), Permission.SOFT_DELETE),
    Granted(UserEntityType(), Permission.SOFT_DELETE),
)


@dataclass(frozen=True)
class AssigningTheRole(When[RolesAndACaller, RBACAdapter, RoleAssignmentNode]):
    @override
    def operation(self) -> str:
        return "assign_role"

    @override
    def describe(self, laid: RolesAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.assignees[0].username} 에게 {laid.role.name} 을 "
            "줍니다",
            english=(
                f"{laid.caller.username} gives {laid.role.name} to {laid.assignees[0].username}"
            ),
        )

    @override
    async def call(self, adapter: RBACAdapter, laid: RolesAndACaller) -> RoleAssignmentNode:
        with ActingAs(laid.caller):
            return await adapter.assign_role(
                AssignRoleInput(user_id=UserID(laid.assignees[0].id), role_id=RoleID(laid.role.id))
            )


@dataclass(frozen=True)
class RevokingTheRole(When[RolesAndACaller, RBACAdapter, RoleAssignmentNode]):
    @override
    def operation(self) -> str:
        return "revoke_role"

    @override
    def describe(self, laid: RolesAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.assignees[0].username} 에게서 {laid.role.name} 을 "
            "회수합니다",
            english=(
                f"{laid.caller.username} takes {laid.role.name} back from "
                f"{laid.assignees[0].username}"
            ),
        )

    @override
    async def call(self, adapter: RBACAdapter, laid: RolesAndACaller) -> RoleAssignmentNode:
        with ActingAs(laid.caller):
            return await adapter.revoke_role(
                RevokeRoleInput(user_id=UserID(laid.assignees[0].id), role_id=RoleID(laid.role.id))
            )


@dataclass(frozen=True)
class AssigningToEveryone(When[RolesAndACaller, RBACAdapter, BulkAssignRoleResultPayload]):
    @override
    def operation(self) -> str:
        return "bulk_assign_role"

    @override
    def describe(self, laid: RolesAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.role.name} 을 미리 저장한 사람들에게 한 번에 줍니다",
            english=(
                f"{laid.caller.username} gives {laid.role.name} to every user seeded in advance "
                "in one call"
            ),
        )

    @override
    async def call(
        self, adapter: RBACAdapter, laid: RolesAndACaller
    ) -> BulkAssignRoleResultPayload:
        with ActingAs(laid.caller):
            return await adapter.bulk_assign_role(
                BulkAssignRoleInput(
                    role_id=RoleID(laid.role.id),
                    user_ids=[UserID(user.id) for user in laid.assignees],
                )
            )


@dataclass(frozen=True)
class RevokingFromEveryone(When[RolesAndACaller, RBACAdapter, BulkRevokeRoleResultPayload]):
    @override
    def operation(self) -> str:
        return "bulk_revoke_role"

    @override
    def describe(self, laid: RolesAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.role.name} 을 미리 저장한 사람들에게서 한 번에 "
            "회수합니다",
            english=(
                f"{laid.caller.username} takes {laid.role.name} back from every user seeded in "
                "advance in one call"
            ),
        )

    @override
    async def call(
        self, adapter: RBACAdapter, laid: RolesAndACaller
    ) -> BulkRevokeRoleResultPayload:
        with ActingAs(laid.caller):
            return await adapter.bulk_revoke_role(
                BulkRevokeRoleInput(
                    role_id=RoleID(laid.role.id),
                    user_ids=[UserID(user.id) for user in laid.assignees],
                )
            )


@dataclass(frozen=True)
class TheAssignment(Then[RolesAndACaller, RoleAssignmentNode]):
    started: datetime
    by_caller: bool = True

    @override
    def says(self) -> str:
        return Says(
            "그 사람과 역할을 잇는 배정 전체가 옵니다",
            english="the whole assignment joining that user and role comes back",
        )

    @override
    def look(self, laid: RolesAndACaller, answered: Answered[RoleAssignmentNode]) -> list[Verdict]:
        node = answered.response
        if not isinstance(node, RoleAssignmentNode):
            return [Refused(NotEnoughPermission, answered.raised)]
        return AssignmentLook(self.started).verdicts(
            "",
            node,
            laid.assignees[0].id,
            laid.role.id,
            laid.caller.id if self.by_caller else None,
        )


@dataclass(frozen=True)
class EveryoneIsAssigned(Then[RolesAndACaller, BulkAssignRoleResultPayload]):
    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "미리 저장한 사람 모두에게 배정이 가고 실패가 없습니다",
            english="every user seeded in advance is assigned and nothing failed",
        )

    @override
    def look(
        self, laid: RolesAndACaller, answered: Answered[BulkAssignRoleResultPayload]
    ) -> list[Verdict]:
        payload = answered.response
        if not isinstance(payload, BulkAssignRoleResultPayload):
            return [Refused(NotEnoughPermission, answered.raised)]
        order = {user.id: index for index, user in enumerate(laid.assignees)}
        assigned = sorted(payload.assigned, key=lambda node: order.get(node.user_id, len(order)))
        verdicts: list[Verdict] = [
            Same("assigned count", len(assigned), len(laid.assignees)),
            Same("failed", payload.failed, []),
        ]
        look = AssignmentLook(self.started)
        for i, (node, user) in enumerate(zip(assigned, laid.assignees, strict=False)):
            verdicts += look.verdicts(
                f"assigned[{i}].", node, user.id, laid.role.id, laid.caller.id
            )
        return verdicts


@dataclass(frozen=True)
class TheOneAlreadyHoldingFails(Then[RolesAndACaller, BulkAssignRoleResultPayload]):
    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "역할을 이미 가진 사람만 실패 목록에 오고 나머지는 배정됩니다",
            english=(
                "only the user who already holds the role comes back failed and the rest are "
                "assigned"
            ),
        )

    @override
    def look(
        self, laid: RolesAndACaller, answered: Answered[BulkAssignRoleResultPayload]
    ) -> list[Verdict]:
        payload = answered.response
        if not isinstance(payload, BulkAssignRoleResultPayload):
            return [Refused(NotEnoughPermission, answered.raised)]
        holder, newcomer = laid.assignees[0], laid.assignees[1]
        verdicts: list[Verdict] = [
            Same("assigned count", len(payload.assigned), 1),
            Same("failed count", len(payload.failed), 1),
        ]
        if payload.assigned:
            verdicts += AssignmentLook(self.started).verdicts(
                "assigned[0].",
                payload.assigned[0],
                newcomer.id,
                laid.role.id,
                laid.caller.id,
            )
        for i, failure in enumerate(payload.failed):
            verdicts += [
                Held[UUID](
                    f"failed[{i}].user_id",
                    failure.user_id,
                    SameAs(
                        holder.id,
                        Says(
                            "미리 저장한 사용자의 id",
                            english="the id of the user seeded in advance",
                        ),
                    ),
                ),
                Held(f"failed[{i}].message", failure.message, Mentions("already assigned")),
            ]
        return verdicts


@dataclass(frozen=True)
class EveryoneIsRevoked(Then[RolesAndACaller, BulkRevokeRoleResultPayload]):
    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "미리 저장한 사람 모두에게서 회수되고 실패가 없습니다",
            english="the role is taken back from every user seeded in advance and nothing failed",
        )

    @override
    def look(
        self, laid: RolesAndACaller, answered: Answered[BulkRevokeRoleResultPayload]
    ) -> list[Verdict]:
        payload = answered.response
        if not isinstance(payload, BulkRevokeRoleResultPayload):
            return [Refused(NotEnoughPermission, answered.raised)]
        verdicts: list[Verdict] = [
            Same("revoked count", len(payload.revoked), len(laid.assignees)),
            Same("failed", payload.failed, []),
        ]
        look = AssignmentLook(self.started)
        for i, (node, user) in enumerate(zip(payload.revoked, laid.assignees, strict=False)):
            verdicts += look.verdicts(f"revoked[{i}].", node, user.id, laid.role.id, None)
        return verdicts


@dataclass(frozen=True)
class TheOneNotHoldingFails(Then[RolesAndACaller, BulkRevokeRoleResultPayload]):
    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "역할을 가지지 않은 사람만 실패 목록에 오고 나머지는 회수됩니다",
            english=(
                "only the user who did not hold the role comes back failed and the rest are "
                "taken back"
            ),
        )

    @override
    def look(
        self, laid: RolesAndACaller, answered: Answered[BulkRevokeRoleResultPayload]
    ) -> list[Verdict]:
        payload = answered.response
        if not isinstance(payload, BulkRevokeRoleResultPayload):
            return [Refused(NotEnoughPermission, answered.raised)]
        holder, other = laid.assignees[0], laid.assignees[1]
        verdicts: list[Verdict] = [
            Same("revoked count", len(payload.revoked), 1),
            Same("failed count", len(payload.failed), 1),
        ]
        for i, failure in enumerate(payload.failed):
            verdicts += [
                Held[UUID](
                    f"failed[{i}].user_id",
                    failure.user_id,
                    SameAs(
                        other.id,
                        Says(
                            "미리 저장한 사용자의 id",
                            english="the id of the user seeded in advance",
                        ),
                    ),
                ),
                Held(f"failed[{i}].message", failure.message, Mentions("not assigned")),
            ]
        for i, node in enumerate(payload.revoked):
            verdicts += AssignmentLook(self.started).verdicts(
                f"revoked[{i}].", node, holder.id, laid.role.id, None
            )
        return verdicts


@dataclass(frozen=True)
class AUserGrantedAssignmentWritesAssignsARole(
    Scenario[TestSeedingSession, RolesAndACaller, RBACAdapter, RoleAssignmentNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-assignment-writes-assigns-a-role"

    @override
    def describe(self) -> str:
        return Says(
            "대상 도메인에서 역할과 사용자에 대한 쓰기 권한을 받은 사용자가 역할을 주면, "
            "그 배정 전체가 옵니다",
            english=(
                "when a user granted write permission on the role and the user gives a role, the "
                "whole assignment comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, RolesAndACaller]:
        return RolesAndSomeone(assignees=1, grant=GRANTING)

    @override
    def when(self) -> When[RolesAndACaller, RBACAdapter, RoleAssignmentNode]:
        return AssigningTheRole()

    @override
    def then(self) -> Then[RolesAndACaller, RoleAssignmentNode]:
        return TheAssignment(started=self.started)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotAssignARole(
    Scenario[TestSeedingSession, RolesAndACaller, RBACAdapter, RoleAssignmentNode]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-assign-a-role"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자는 역할을 줄 수 없습니다",
            english="a user granted nothing cannot give a role",
        )

    @override
    def given(self) -> Given[TestSeedingSession, RolesAndACaller]:
        return RolesAndSomeone(assignees=1)

    @override
    def when(self) -> When[RolesAndACaller, RBACAdapter, RoleAssignmentNode]:
        return AssigningTheRole()

    @override
    def then(self) -> Then[RolesAndACaller, RoleAssignmentNode]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AssigningARoleAlreadyHeldIsRefused(
    Scenario[TestSeedingSession, RolesAndACaller, RBACAdapter, RoleAssignmentNode]
):
    @override
    def summary(self) -> str:
        return "assigning-a-role-the-user-already-holds-is-refused"

    @override
    def describe(self) -> str:
        return Says(
            "이미 역할을 가진 사람에게 같은 역할을 다시 주면 거부됩니다",
            english="giving a role to a user who already holds it is rejected",
        )

    @override
    def given(self) -> Given[TestSeedingSession, RolesAndACaller]:
        return RolesAndSomeone(assignees=1, assigned=1, grant=GRANTING)

    @override
    def when(self) -> When[RolesAndACaller, RBACAdapter, RoleAssignmentNode]:
        return AssigningTheRole()

    @override
    def then(self) -> Then[RolesAndACaller, RoleAssignmentNode]:
        return TheCallIsRefused(RoleAlreadyAssigned)


@dataclass(frozen=True)
class AUserGrantedRevocationWritesRevokesARole(
    Scenario[TestSeedingSession, RolesAndACaller, RBACAdapter, RoleAssignmentNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-revocation-writes-revokes-a-role"

    @override
    def describe(self) -> str:
        return Says(
            "대상 도메인에서 역할과 사용자에 대한 지우기 권한을 받은 사용자가 역할을 회수하면, "
            "그 배정 전체가 옵니다",
            english=(
                "when a user granted delete permission on the role and the user takes a role "
                "back, the whole assignment comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, RolesAndACaller]:
        return RolesAndSomeone(assignees=1, assigned=1, grant=REVOKING)

    @override
    def when(self) -> When[RolesAndACaller, RBACAdapter, RoleAssignmentNode]:
        return RevokingTheRole()

    @override
    def then(self) -> Then[RolesAndACaller, RoleAssignmentNode]:
        return TheAssignment(started=self.started, by_caller=False)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotRevokeARole(
    Scenario[TestSeedingSession, RolesAndACaller, RBACAdapter, RoleAssignmentNode]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-revoke-a-role"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자는 역할을 회수할 수 없습니다",
            english="a user granted nothing cannot take a role back",
        )

    @override
    def given(self) -> Given[TestSeedingSession, RolesAndACaller]:
        return RolesAndSomeone(assignees=1, assigned=1)

    @override
    def when(self) -> When[RolesAndACaller, RBACAdapter, RoleAssignmentNode]:
        return RevokingTheRole()

    @override
    def then(self) -> Then[RolesAndACaller, RoleAssignmentNode]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class RevokingARoleNotHeldIsRefused(
    Scenario[TestSeedingSession, RolesAndACaller, RBACAdapter, RoleAssignmentNode]
):
    @override
    def summary(self) -> str:
        return "revoking-a-role-the-user-does-not-hold-is-refused"

    @override
    def describe(self) -> str:
        return Says(
            "역할을 가지지 않은 사람에게서 그 역할을 회수하면 거부됩니다",
            english="taking a role back from a user who does not hold it is rejected",
        )

    @override
    def given(self) -> Given[TestSeedingSession, RolesAndACaller]:
        return RolesAndSomeone(assignees=1, grant=REVOKING)

    @override
    def when(self) -> When[RolesAndACaller, RBACAdapter, RoleAssignmentNode]:
        return RevokingTheRole()

    @override
    def then(self) -> Then[RolesAndACaller, RoleAssignmentNode]:
        return TheCallIsRefused(RoleNotAssigned)


@dataclass(frozen=True)
class AUserGrantedAssignmentWritesAssignsToEveryone(
    Scenario[TestSeedingSession, RolesAndACaller, RBACAdapter, BulkAssignRoleResultPayload]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-assignment-writes-assigns-a-role-to-everyone"

    @override
    def describe(self) -> str:
        return Says(
            "대상 도메인에서 역할과 사용자에 대한 쓰기 권한을 받은 사용자가 역할을 여럿에게 "
            "한 번에 주면, 모두 배정되고 실패가 없습니다",
            english=(
                "when a user granted write permission on the role and the users gives a role to "
                "several users in one call, everyone is assigned and nothing failed"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, RolesAndACaller]:
        return RolesAndSomeone(assignees=2, grant=GRANTING)

    @override
    def when(self) -> When[RolesAndACaller, RBACAdapter, BulkAssignRoleResultPayload]:
        return AssigningToEveryone()

    @override
    def then(self) -> Then[RolesAndACaller, BulkAssignRoleResultPayload]:
        return EveryoneIsAssigned(started=self.started)


@dataclass(frozen=True)
class AssigningToEveryoneAnswersForTheOneHolding(
    Scenario[TestSeedingSession, RolesAndACaller, RBACAdapter, BulkAssignRoleResultPayload]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "assigning-to-several-users-answers-for-the-one-already-holding"

    @override
    def describe(self) -> str:
        return Says(
            "여럿에게 역할을 한 번에 줄 때 이미 역할을 가진 사람은 실패 목록에 오고 나머지는 "
            "배정됩니다",
            english=(
                "when a role is given to several users in one call, the user who already holds it "
                "comes back failed and the rest are assigned"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, RolesAndACaller]:
        return RolesAndSomeone(assignees=2, assigned=1, grant=GRANTING)

    @override
    def when(self) -> When[RolesAndACaller, RBACAdapter, BulkAssignRoleResultPayload]:
        return AssigningToEveryone()

    @override
    def then(self) -> Then[RolesAndACaller, BulkAssignRoleResultPayload]:
        return TheOneAlreadyHoldingFails(started=self.started)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotAssignToEveryone(
    Scenario[TestSeedingSession, RolesAndACaller, RBACAdapter, BulkAssignRoleResultPayload]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-assign-a-role-to-several-users"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자는 역할을 여럿에게 한 번에 줄 수 없습니다",
            english="a user granted nothing cannot give a role to several users in one call",
        )

    @override
    def given(self) -> Given[TestSeedingSession, RolesAndACaller]:
        return RolesAndSomeone(assignees=2)

    @override
    def when(self) -> When[RolesAndACaller, RBACAdapter, BulkAssignRoleResultPayload]:
        return AssigningToEveryone()

    @override
    def then(self) -> Then[RolesAndACaller, BulkAssignRoleResultPayload]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AUserGrantedRevocationWritesRevokesFromEveryone(
    Scenario[TestSeedingSession, RolesAndACaller, RBACAdapter, BulkRevokeRoleResultPayload]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-revocation-writes-revokes-a-role-from-everyone"

    @override
    def describe(self) -> str:
        return Says(
            "대상 도메인에서 역할과 사용자에 대한 지우기 권한을 받은 사용자가 역할을 여럿에게서 "
            "한 번에 회수하면, 모두 회수되고 실패가 없습니다",
            english=(
                "when a user granted delete permission on the role and the users takes a role "
                "back from several users in one call, everyone is revoked and nothing failed"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, RolesAndACaller]:
        return RolesAndSomeone(assignees=2, assigned=2, grant=REVOKING)

    @override
    def when(self) -> When[RolesAndACaller, RBACAdapter, BulkRevokeRoleResultPayload]:
        return RevokingFromEveryone()

    @override
    def then(self) -> Then[RolesAndACaller, BulkRevokeRoleResultPayload]:
        return EveryoneIsRevoked(started=self.started)


@dataclass(frozen=True)
class RevokingFromEveryoneAnswersForTheOneNotHolding(
    Scenario[TestSeedingSession, RolesAndACaller, RBACAdapter, BulkRevokeRoleResultPayload]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "revoking-from-several-users-answers-for-the-one-not-holding"

    @override
    def describe(self) -> str:
        return Says(
            "여럿에게서 역할을 한 번에 회수할 때 역할을 가지지 않은 사람은 실패 목록에 오고 "
            "나머지는 회수됩니다",
            english=(
                "when a role is taken back from several users in one call, the user who did not "
                "hold it comes back failed and the rest are taken back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, RolesAndACaller]:
        return RolesAndSomeone(assignees=2, assigned=1, grant=REVOKING)

    @override
    def when(self) -> When[RolesAndACaller, RBACAdapter, BulkRevokeRoleResultPayload]:
        return RevokingFromEveryone()

    @override
    def then(self) -> Then[RolesAndACaller, BulkRevokeRoleResultPayload]:
        return TheOneNotHoldingFails(started=self.started)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotRevokeFromEveryone(
    Scenario[TestSeedingSession, RolesAndACaller, RBACAdapter, BulkRevokeRoleResultPayload]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-revoke-a-role-from-several-users"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자는 역할을 여럿에게서 한 번에 회수할 수 없습니다",
            english="a user granted nothing cannot take a role back from several users in one call",
        )

    @override
    def given(self) -> Given[TestSeedingSession, RolesAndACaller]:
        return RolesAndSomeone(assignees=2, assigned=2)

    @override
    def when(self) -> When[RolesAndACaller, RBACAdapter, BulkRevokeRoleResultPayload]:
        return RevokingFromEveryone()

    @override
    def then(self) -> Then[RolesAndACaller, BulkRevokeRoleResultPayload]:
        return TheCallIsRefused(NotEnoughPermission)


SCENARIOS: list[AssignmentStep] = [
    AUserGrantedAssignmentWritesAssignsARole(started=datetime.now(UTC)),
    AUserGrantedNothingMayNotAssignARole(),
    AssigningARoleAlreadyHeldIsRefused(),
    AUserGrantedRevocationWritesRevokesARole(started=datetime.now(UTC)),
    AUserGrantedNothingMayNotRevokeARole(),
    RevokingARoleNotHeldIsRefused(),
    AUserGrantedAssignmentWritesAssignsToEveryone(started=datetime.now(UTC)),
    AssigningToEveryoneAnswersForTheOneHolding(started=datetime.now(UTC)),
    AUserGrantedNothingMayNotAssignToEveryone(),
    AUserGrantedRevocationWritesRevokesFromEveryone(started=datetime.now(UTC)),
    RevokingFromEveryoneAnswersForTheOneNotHolding(started=datetime.now(UTC)),
    AUserGrantedNothingMayNotRevokeFromEveryone(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_assigning(
    scenario: AssignmentStep, adapter: RBACAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
