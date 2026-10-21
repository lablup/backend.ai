"""역할 여럿 soft delete, restore, purge."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override
from uuid import UUID

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.common import PartialBulkPayload
from ai.backend.common.dto.manager.v2.rbac.request import (
    PartialBulkDeleteRolesInput,
    PartialBulkPurgeRolesInput,
    PartialBulkRestoreRolesInput,
)
from ai.backend.common.dto.manager.v2.rbac.response import RoleNode
from ai.backend.manager.api.adapters.rbac.adapter import RBACAdapter
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
from bai_scenario.components.rbac import (
    NothingIsProcessed,
    RoleLook,
    RolesAndACaller,
    RolesAndSomeone,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Deleted = PartialBulkPayload[RoleNode]
type RoleStep = Scenario[TestSeedingSession, RolesAndACaller, RBACAdapter, Deleted]


@dataclass(frozen=True)
class SoftDeletingEveryRole(When[RolesAndACaller, RBACAdapter, Deleted]):
    """역할들을 한 번에 soft delete 한다. `missing`이 있으면 그 id 도 함께 넣는다."""

    missing: UUID | None = None

    @override
    def operation(self) -> str:
        return "partial_bulk_delete"

    @override
    def describe(self, laid: RolesAndACaller) -> str:
        besides = " 와 없는 id 하나" if self.missing is not None else ""
        return (
            f"{laid.caller.username}이 역할 {len(laid.roles)}개{besides}를 한 번에 soft delete 함"
        )

    @override
    async def call(self, adapter: RBACAdapter, laid: RolesAndACaller) -> Deleted:
        ids: list[UUID] = [role.id for role in laid.roles]
        if self.missing is not None:
            ids.append(self.missing)
        with ActingAs(laid.caller):
            return await adapter.partial_bulk_delete(PartialBulkDeleteRolesInput(ids=ids))


@dataclass(frozen=True)
class SoftDeletingThenRestoringEveryRole(When[RolesAndACaller, RBACAdapter, Deleted]):
    """역할들을 한 번에 soft delete 했다가 한 번에 restore 한다. restore 의 답을 준다."""

    @override
    def operation(self) -> str:
        return "partial_bulk_restore"

    @override
    def describe(self, laid: RolesAndACaller) -> str:
        return (
            f"{laid.caller.username}이 역할 {len(laid.roles)}개를 한 번에 soft delete "
            "했다가 한 번에 restore 함"
        )

    @override
    async def call(self, adapter: RBACAdapter, laid: RolesAndACaller) -> Deleted:
        ids: list[UUID] = [role.id for role in laid.roles]
        with ActingAs(laid.caller):
            await adapter.partial_bulk_delete(PartialBulkDeleteRolesInput(ids=ids))
            return await adapter.partial_bulk_restore(PartialBulkRestoreRolesInput(ids=ids))


@dataclass(frozen=True)
class PurgingEveryRole(When[RolesAndACaller, RBACAdapter, Deleted]):
    """역할들을 한 번에 purge 한다."""

    @override
    def operation(self) -> str:
        return "partial_bulk_purge"

    @override
    def describe(self, laid: RolesAndACaller) -> str:
        return f"{laid.caller.username}이 역할 {len(laid.roles)}개를 한 번에 purge 함"

    @override
    async def call(self, adapter: RBACAdapter, laid: RolesAndACaller) -> Deleted:
        with ActingAs(laid.caller):
            return await adapter.partial_bulk_purge(
                PartialBulkPurgeRolesInput(ids=[role.id for role in laid.roles])
            )


@dataclass(frozen=True)
class EveryRoleComesBack(Then[RolesAndACaller, Deleted]):
    """역할이 모두 처리된 목록에 온다. `missing`이 있으면 그 id 만 실패 목록에 온다."""

    started: datetime
    deleted: bool
    missing: UUID | None = None

    @override
    def says(self) -> str:
        state = "soft delete 된 상태" if self.deleted else "활성"
        if self.missing is None:
            return f"역할이 모두 {state}로 오고, 실패한 것은 없다"
        return f"역할이 모두 {state}로 오고, 없는 id 는 대상이 없다는 이유로 실패 목록에 온다"

    @override
    def look(self, laid: RolesAndACaller, answered: Answered[Deleted]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        look = RoleLook(self.started, deleted=self.deleted)
        verdicts: list[Verdict] = [Same("successes count", len(payload.successes), len(laid.roles))]
        for i, (node, role) in enumerate(zip(payload.successes, laid.roles, strict=False)):
            verdicts += look.verdicts(f"successes[{i}].", node, role, laid.domain)
        if self.missing is None:
            return [*verdicts, Same("failed", payload.failed, [])]
        verdicts.append(Same("failed count", len(payload.failed), 1))
        for failure in payload.failed:
            verdicts += [
                Held[UUID]("failed[0].id", failure.id, SameAs(self.missing, "요청에 넣은 없는 id")),
                Held("failed[0].message", failure.message, Mentions("not found")),
            ]
        return verdicts


@dataclass(frozen=True)
class SoftDeletingAnswersForTheMissingOne(
    Scenario[TestSeedingSession, RolesAndACaller, RBACAdapter, Deleted]
):
    started: datetime
    missing: UUID = UUID(int=1)

    @override
    def summary(self) -> str:
        return "soft-deleting-several-answers-for-the-missing-one"

    @override
    def describe(self) -> str:
        return (
            "활성 역할 둘과 없는 id 하나를 한 번에 soft delete 하면, 둘은 soft delete 된 채로 오고 "
            "없는 id 는 대상이 없다는 이유로 실패 목록에 온다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, RolesAndACaller]:
        return RolesAndSomeone(role=UserRole.SUPERADMIN, count=2)

    @override
    def when(self) -> When[RolesAndACaller, RBACAdapter, Deleted]:
        return SoftDeletingEveryRole(missing=self.missing)

    @override
    def then(self) -> Then[RolesAndACaller, Deleted]:
        return EveryRoleComesBack(started=self.started, deleted=True, missing=self.missing)


@dataclass(frozen=True)
class AUserGrantedNothingSoftDeletesNone(
    Scenario[TestSeedingSession, RolesAndACaller, RBACAdapter, Deleted]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-soft-deletes-none-of-several-roles"

    @override
    def describe(self) -> str:
        return (
            "아무 권한도 받지 않은 사용자가 역할 여럿을 한 번에 soft delete 하려 하면, "
            "soft delete 된 것 없이 모두 권한이 없다는 이유로 실패 목록에 온다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, RolesAndACaller]:
        return RolesAndSomeone(count=2)

    @override
    def when(self) -> When[RolesAndACaller, RBACAdapter, Deleted]:
        return SoftDeletingEveryRole()

    @override
    def then(self) -> Then[RolesAndACaller, Deleted]:
        return NothingIsProcessed(reason="Insufficient permission")


@dataclass(frozen=True)
class RestoringBringsSeveralBack(
    Scenario[TestSeedingSession, RolesAndACaller, RBACAdapter, Deleted]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "restoring-several-brings-them-back"

    @override
    def describe(self) -> str:
        return "soft delete 된 역할 여럿을 한 번에 restore 하면, 모두 활성으로 온다"

    @override
    def given(self) -> Given[TestSeedingSession, RolesAndACaller]:
        return RolesAndSomeone(role=UserRole.SUPERADMIN, count=2)

    @override
    def when(self) -> When[RolesAndACaller, RBACAdapter, Deleted]:
        return SoftDeletingThenRestoringEveryRole()

    @override
    def then(self) -> Then[RolesAndACaller, Deleted]:
        return EveryRoleComesBack(started=self.started, deleted=False)


@dataclass(frozen=True)
class TheSuperadminPurgesSeveralRoles(
    Scenario[TestSeedingSession, RolesAndACaller, RBACAdapter, Deleted]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-purges-several-roles-at-once"

    @override
    def describe(self) -> str:
        return (
            "슈퍼관리자가 역할 여럿을 한 번에 purge 하면, 모두 처리된 목록에 오고 실패한 것은 없다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, RolesAndACaller]:
        return RolesAndSomeone(role=UserRole.SUPERADMIN, count=2)

    @override
    def when(self) -> When[RolesAndACaller, RBACAdapter, Deleted]:
        return PurgingEveryRole()

    @override
    def then(self) -> Then[RolesAndACaller, Deleted]:
        return EveryRoleComesBack(started=self.started, deleted=False)


@dataclass(frozen=True)
class AUserGrantedNothingPurgesNone(
    Scenario[TestSeedingSession, RolesAndACaller, RBACAdapter, Deleted]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-purges-none-of-several-roles"

    @override
    def describe(self) -> str:
        return (
            "아무 권한도 받지 않은 사용자가 역할 여럿을 한 번에 purge 하려 하면, "
            "purge 된 것 없이 모두 권한이 없다는 이유로 실패 목록에 온다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, RolesAndACaller]:
        return RolesAndSomeone(count=2)

    @override
    def when(self) -> When[RolesAndACaller, RBACAdapter, Deleted]:
        return PurgingEveryRole()

    @override
    def then(self) -> Then[RolesAndACaller, Deleted]:
        return NothingIsProcessed(reason="Insufficient permission")


SCENARIOS: list[RoleStep] = [
    SoftDeletingAnswersForTheMissingOne(started=datetime.now(UTC)),
    AUserGrantedNothingSoftDeletesNone(),
    RestoringBringsSeveralBack(started=datetime.now(UTC)),
    TheSuperadminPurgesSeveralRoles(started=datetime.now(UTC)),
    AUserGrantedNothingPurgesNone(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_partial_bulk_deleting(
    scenario: RoleStep, adapter: RBACAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
