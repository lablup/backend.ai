"""역할 soft delete, restore, purge."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override
from uuid import UUID

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.rbac.response import (
    DeleteRolePayload,
    PurgeRolePayload,
    RestoreRolePayload,
)
from ai.backend.manager.api.adapters.rbac.adapter import RBACAdapter
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    Refused,
    SameAs,
    Says,
    Scenario,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.domain import TheCallIsRefused
from bai_scenario.components.rbac import RolesAndACaller, RolesAndSomeone
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Deleted = DeleteRolePayload | RestoreRolePayload | PurgeRolePayload
type RoleStep = Scenario[TestSeedingSession, RolesAndACaller, RBACAdapter, Deleted]


@dataclass(frozen=True)
class SoftDeleting(When[RolesAndACaller, RBACAdapter, Deleted]):
    """역할을 soft delete 한다."""

    @override
    def operation(self) -> str:
        return "delete"

    @override
    def describe(self, laid: RolesAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.role.name} 을 soft delete 합니다",
            english=f"{laid.caller.username} soft deletes {laid.role.name}",
        )

    @override
    async def call(self, adapter: RBACAdapter, laid: RolesAndACaller) -> Deleted:
        with ActingAs(laid.caller):
            return await adapter.delete(laid.role.id)


@dataclass(frozen=True)
class SoftDeletingThenRestoring(When[RolesAndACaller, RBACAdapter, Deleted]):
    """soft delete 했다가 restore 한다. restore 의 답을 준다."""

    @override
    def operation(self) -> str:
        return "restore"

    @override
    def describe(self, laid: RolesAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.role.name} 을 soft delete 했다가 restore 합니다",
            english=f"{laid.caller.username} soft deletes {laid.role.name} and then restores it",
        )

    @override
    async def call(self, adapter: RBACAdapter, laid: RolesAndACaller) -> Deleted:
        with ActingAs(laid.caller):
            await adapter.delete(laid.role.id)
            return await adapter.restore(laid.role.id)


@dataclass(frozen=True)
class Restoring(When[RolesAndACaller, RBACAdapter, Deleted]):
    """restore 한다."""

    @override
    def operation(self) -> str:
        return "restore"

    @override
    def describe(self, laid: RolesAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.role.name} 을 restore 합니다",
            english=f"{laid.caller.username} restores {laid.role.name}",
        )

    @override
    async def call(self, adapter: RBACAdapter, laid: RolesAndACaller) -> Deleted:
        with ActingAs(laid.caller):
            return await adapter.restore(laid.role.id)


@dataclass(frozen=True)
class Purging(When[RolesAndACaller, RBACAdapter, Deleted]):
    """purge 한다."""

    @override
    def operation(self) -> str:
        return "purge"

    @override
    def describe(self, laid: RolesAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.role.name} 을 purge 합니다",
            english=f"{laid.caller.username} purges {laid.role.name}",
        )

    @override
    async def call(self, adapter: RBACAdapter, laid: RolesAndACaller) -> Deleted:
        with ActingAs(laid.caller):
            return await adapter.purge(laid.role.id)


@dataclass(frozen=True)
class TheRoleIdComesBack(Then[RolesAndACaller, Deleted]):
    """그 역할의 id 가 온다. 답이 실은 것은 그 하나뿐이다."""

    @override
    def says(self) -> str:
        return Says("그 역할의 id 가 옵니다", english="the id of that role comes back")

    @override
    def look(self, laid: RolesAndACaller, answered: Answered[Deleted]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        return [
            Held[UUID](
                "id",
                payload.id,
                SameAs(
                    laid.role.id,
                    Says("대상 역할의 id", english="the id of the target role"),
                ),
            )
        ]


@dataclass(frozen=True)
class TheSuperadminSoftDeletesARole(
    Scenario[TestSeedingSession, RolesAndACaller, RBACAdapter, Deleted]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-soft-deletes-a-role"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 역할을 soft delete 하면, 그 역할의 id 가 옵니다",
            english="when the superadmin soft deletes a role, the id of that role comes back",
        )

    @override
    def given(self) -> Given[TestSeedingSession, RolesAndACaller]:
        return RolesAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[RolesAndACaller, RBACAdapter, Deleted]:
        return SoftDeleting()

    @override
    def then(self) -> Then[RolesAndACaller, Deleted]:
        return TheRoleIdComesBack()


@dataclass(frozen=True)
class AUserGrantedNothingMayNotSoftDelete(
    Scenario[TestSeedingSession, RolesAndACaller, RBACAdapter, Deleted]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-soft-delete-a-role"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자는 역할을 soft delete 할 수 없습니다",
            english="a user granted nothing cannot soft delete a role",
        )

    @override
    def given(self) -> Given[TestSeedingSession, RolesAndACaller]:
        return RolesAndSomeone()

    @override
    def when(self) -> When[RolesAndACaller, RBACAdapter, Deleted]:
        return SoftDeleting()

    @override
    def then(self) -> Then[RolesAndACaller, Deleted]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class RestoringASoftDeletedRole(
    Scenario[TestSeedingSession, RolesAndACaller, RBACAdapter, Deleted]
):
    @override
    def summary(self) -> str:
        return "restoring-a-soft-deleted-role"

    @override
    def describe(self) -> str:
        return Says(
            "soft delete 된 역할을 restore 하면, 그 역할의 id 가 옵니다",
            english="when a soft-deleted role is restored, the id of that role comes back",
        )

    @override
    def given(self) -> Given[TestSeedingSession, RolesAndACaller]:
        return RolesAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[RolesAndACaller, RBACAdapter, Deleted]:
        return SoftDeletingThenRestoring()

    @override
    def then(self) -> Then[RolesAndACaller, Deleted]:
        return TheRoleIdComesBack()


@dataclass(frozen=True)
class AUserGrantedNothingMayNotRestore(
    Scenario[TestSeedingSession, RolesAndACaller, RBACAdapter, Deleted]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-restore-a-role"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자는 역할을 restore 할 수 없습니다",
            english="a user granted nothing cannot restore a role",
        )

    @override
    def given(self) -> Given[TestSeedingSession, RolesAndACaller]:
        return RolesAndSomeone()

    @override
    def when(self) -> When[RolesAndACaller, RBACAdapter, Deleted]:
        return Restoring()

    @override
    def then(self) -> Then[RolesAndACaller, Deleted]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class TheSuperadminPurgesARole(Scenario[TestSeedingSession, RolesAndACaller, RBACAdapter, Deleted]):
    @override
    def summary(self) -> str:
        return "the-superadmin-purges-a-role"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 역할을 purge 하면, 그 역할의 id 가 옵니다",
            english="when the superadmin purges a role, the id of that role comes back",
        )

    @override
    def given(self) -> Given[TestSeedingSession, RolesAndACaller]:
        return RolesAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[RolesAndACaller, RBACAdapter, Deleted]:
        return Purging()

    @override
    def then(self) -> Then[RolesAndACaller, Deleted]:
        return TheRoleIdComesBack()


@dataclass(frozen=True)
class AUserGrantedNothingMayNotPurge(
    Scenario[TestSeedingSession, RolesAndACaller, RBACAdapter, Deleted]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-purge-a-role"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자는 역할을 purge 할 수 없습니다",
            english="a user granted nothing cannot purge a role",
        )

    @override
    def given(self) -> Given[TestSeedingSession, RolesAndACaller]:
        return RolesAndSomeone()

    @override
    def when(self) -> When[RolesAndACaller, RBACAdapter, Deleted]:
        return Purging()

    @override
    def then(self) -> Then[RolesAndACaller, Deleted]:
        return TheCallIsRefused(NotEnoughPermission)


SCENARIOS: list[RoleStep] = [
    TheSuperadminSoftDeletesARole(),
    AUserGrantedNothingMayNotSoftDelete(),
    RestoringASoftDeletedRole(),
    AUserGrantedNothingMayNotRestore(),
    TheSuperadminPurgesARole(),
    AUserGrantedNothingMayNotPurge(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_deleting(
    scenario: RoleStep, adapter: RBACAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
