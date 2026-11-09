"""리소스 그룹 완전 삭제 — 완전 삭제만 있고 soft delete는 없다."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override

import pytest

from ai.backend.common.data.permission.types import Permission
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.resource_group.response import ResourceGroupDetailNode
from ai.backend.manager.api.adapters.resource_group.adapter import ResourceGroupAdapter
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Says, Scenario, Then, When
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.resource_group import (
    AGroupAndACaller,
    AGroupAndSomeone,
    GroupLook,
    TheGroupNode,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type RetiringStep = Scenario[
    TestSeedingSession, AGroupAndACaller, ResourceGroupAdapter, ResourceGroupDetailNode
]

UNKNOWN = "no-such-group"


@dataclass(frozen=True)
class Purging(When[AGroupAndACaller, ResourceGroupAdapter, ResourceGroupDetailNode]):
    """완전 삭제한다. ``unknown``이면 어느 행에도 없는 이름을 쓴다."""

    unknown: bool = False

    @override
    def operation(self) -> str:
        return "purge"

    @override
    def describe(self, laid: AGroupAndACaller) -> str:
        target_ko = "존재하지 않는 이름" if self.unknown else laid.group.name
        target_en = "a name that does not exist" if self.unknown else laid.group.name
        return Says(
            f"{laid.caller.username}이 {target_ko}을 완전 삭제합니다",
            english=f"{laid.caller.username} purges {target_en}",
        )

    @override
    async def call(
        self, adapter: ResourceGroupAdapter, laid: AGroupAndACaller
    ) -> ResourceGroupDetailNode:
        with ActingAs(laid.caller):
            return await adapter.purge(
                await adapter.lookup_name(UNKNOWN if self.unknown else laid.group.name)
            )


@dataclass(frozen=True)
class TheSuperadminPurgesAGroup(
    Scenario[TestSeedingSession, AGroupAndACaller, ResourceGroupAdapter, ResourceGroupDetailNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-purges-a-resource-group"

    @override
    def describe(self) -> str:
        return Says(
            "자원 그룹 하나가 있고 superadmin 이 완전 삭제하면 삭제한 그룹 전체가 반환됩니다",
            english=(
                "one resource group exists and the superadmin purges it, so the whole deleted "
                "group comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AGroupAndACaller]:
        return AGroupAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AGroupAndACaller, ResourceGroupAdapter, ResourceGroupDetailNode]:
        return Purging()

    @override
    def then(self) -> Then[AGroupAndACaller, ResourceGroupDetailNode]:
        return TheGroupNode(GroupLook(started=self.started))


@dataclass(frozen=True)
class AUserGrantedHardDeleteOnTheGroupPurgesIt(
    Scenario[TestSeedingSession, AGroupAndACaller, ResourceGroupAdapter, ResourceGroupDetailNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-hard-delete-on-the-group-purges-it"

    @override
    def describe(self) -> str:
        return Says(
            "그 자원 그룹에 부여된 역할로 완전 삭제 권한을 받은 사용자가 완전 삭제하면 삭제한 "
            "그룹 전체가 반환됩니다",
            english=(
                "a user granted hard delete through the role granted on the resource group "
                "purging it gets the whole deleted group"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AGroupAndACaller]:
        return AGroupAndSomeone(granted=Permission.HARD_DELETE)

    @override
    def when(self) -> When[AGroupAndACaller, ResourceGroupAdapter, ResourceGroupDetailNode]:
        return Purging()

    @override
    def then(self) -> Then[AGroupAndACaller, ResourceGroupDetailNode]:
        return TheGroupNode(GroupLook(started=self.started))


@dataclass(frozen=True)
class AUserGrantedNothingMayNotPurge(
    Scenario[TestSeedingSession, AGroupAndACaller, ResourceGroupAdapter, ResourceGroupDetailNode]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-purge-a-resource-group"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 없는 사용자가 완전 삭제하려 하면 권한 부족으로 거부됩니다",
            english=(
                "a user granted nothing trying to purge is rejected for not enough permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AGroupAndACaller]:
        return AGroupAndSomeone()

    @override
    def when(self) -> When[AGroupAndACaller, ResourceGroupAdapter, ResourceGroupDetailNode]:
        return Purging()

    @override
    def then(self) -> Then[AGroupAndACaller, ResourceGroupDetailNode]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class TheSuperadminPurgingAnUnknownNameIsNotFound(
    Scenario[TestSeedingSession, AGroupAndACaller, ResourceGroupAdapter, ResourceGroupDetailNode]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-purging-a-name-nothing-answers-to-is-not-found"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 존재하지 않는 이름을 완전 삭제하면 대상을 찾을 수 없다는 이유로 "
            "거부됩니다",
            english=(
                "when the superadmin purges a name nothing answers to, the call is rejected "
                "because no target answers to it"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AGroupAndACaller]:
        return AGroupAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AGroupAndACaller, ResourceGroupAdapter, ResourceGroupDetailNode]:
        return Purging(unknown=True)

    @override
    def then(self) -> Then[AGroupAndACaller, ResourceGroupDetailNode]:
        return TheCallIsRefused(EntityNotFoundError)


SCENARIOS: list[RetiringStep] = [
    TheSuperadminPurgesAGroup(started=datetime.now(UTC)),
    AUserGrantedHardDeleteOnTheGroupPurgesIt(started=datetime.now(UTC)),
    AUserGrantedNothingMayNotPurge(),
    TheSuperadminPurgingAnUnknownNameIsNotFound(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_retiring(
    scenario: RetiringStep, adapter: ResourceGroupAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
