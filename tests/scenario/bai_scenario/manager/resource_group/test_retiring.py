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
from ai.backend.testutils.scenario_steps import Given, Scenario, Then, When
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.resource_group import (
    AGroupAndACaller,
    AGroupAndSomeone,
    GroupLook,
    TheGroupNode,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

type RetiringStep = Scenario[
    SeedingSession, AGroupAndACaller, ResourceGroupAdapter, ResourceGroupDetailNode
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
        target = "존재하지 않는 이름" if self.unknown else laid.group.name
        return f"{laid.caller.username}이 {target} 완전 삭제"

    @override
    async def call(
        self, adapter: ResourceGroupAdapter, laid: AGroupAndACaller
    ) -> ResourceGroupDetailNode:
        with ActingAs(laid.caller):
            return await adapter.purge(UNKNOWN if self.unknown else laid.group.name)


@dataclass(frozen=True)
class TheSuperadminPurgesAGroup(
    Scenario[SeedingSession, AGroupAndACaller, ResourceGroupAdapter, ResourceGroupDetailNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-purges-a-resource-group"

    @override
    def describe(self) -> str:
        return "리소스 그룹 하나가 있고 슈퍼관리자가 완전 삭제하면 지운 그룹 전체가 반환된다"

    @override
    def given(self) -> Given[SeedingSession, AGroupAndACaller]:
        return AGroupAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AGroupAndACaller, ResourceGroupAdapter, ResourceGroupDetailNode]:
        return Purging()

    @override
    def then(self) -> Then[AGroupAndACaller, ResourceGroupDetailNode]:
        return TheGroupNode(GroupLook(started=self.started))


@dataclass(frozen=True)
class AUserGrantedHardDeleteOnTheGroupPurgesIt(
    Scenario[SeedingSession, AGroupAndACaller, ResourceGroupAdapter, ResourceGroupDetailNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-hard-delete-on-the-group-purges-it"

    @override
    def describe(self) -> str:
        return "그 그룹에 앉힌 역할로 완전 삭제 권한을 받은 사용자가 완전 삭제하면 지운 그룹 전체가 반환된다"

    @override
    def given(self) -> Given[SeedingSession, AGroupAndACaller]:
        return AGroupAndSomeone(granted=Permission.HARD_DELETE)

    @override
    def when(self) -> When[AGroupAndACaller, ResourceGroupAdapter, ResourceGroupDetailNode]:
        return Purging()

    @override
    def then(self) -> Then[AGroupAndACaller, ResourceGroupDetailNode]:
        return TheGroupNode(GroupLook(started=self.started))


@dataclass(frozen=True)
class AUserGrantedNothingMayNotPurge(
    Scenario[SeedingSession, AGroupAndACaller, ResourceGroupAdapter, ResourceGroupDetailNode]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-purge-a-resource-group"

    @override
    def describe(self) -> str:
        return "아무 권한도 없는 사용자가 완전 삭제하려 하면 권한 부족으로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, AGroupAndACaller]:
        return AGroupAndSomeone()

    @override
    def when(self) -> When[AGroupAndACaller, ResourceGroupAdapter, ResourceGroupDetailNode]:
        return Purging()

    @override
    def then(self) -> Then[AGroupAndACaller, ResourceGroupDetailNode]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class TheSuperadminPurgingAnUnknownNameIsNotFound(
    Scenario[SeedingSession, AGroupAndACaller, ResourceGroupAdapter, ResourceGroupDetailNode]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-purging-a-name-nothing-answers-to-is-not-found"

    @override
    def describe(self) -> str:
        return (
            "슈퍼관리자가 존재하지 않는 이름을 완전 삭제하면 대상을 찾을 수 없다는 이유로 거부된다"
        )

    @override
    def given(self) -> Given[SeedingSession, AGroupAndACaller]:
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
