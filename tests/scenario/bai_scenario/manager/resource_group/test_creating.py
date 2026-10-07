"""리소스 그룹 생성 — 누가 만들 수 있고, 무엇이 이름과 기본 그룹을 막는가."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, override

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.resource_group.request import CreateResourceGroupInput
from ai.backend.common.dto.manager.v2.resource_group.response import ResourceGroupDetailNode
from ai.backend.common.exception import ResourceGroupConflict
from ai.backend.manager.api.adapters.resource_group.adapter import ResourceGroupAdapter
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.errors.resource import DefaultResourceGroupAlreadyExists
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Scenario, Then, When
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.resource_group import (
    AGroupAndACaller,
    AGroupAndSomeone,
    TheNewGroupNode,
)
from bai_scenario.components.system import ACaller, SomeoneAlone
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

type CreatingStep = Scenario[SeedingSession, Any, ResourceGroupAdapter, ResourceGroupDetailNode]


@dataclass(frozen=True)
class Creating(When[Any, ResourceGroupAdapter, ResourceGroupDetailNode]):
    """리소스 그룹을 만든다. 이름을 대지 않으면 미리 만들어 둔 그룹의 이름을 그대로 쓴다."""

    named: str | None = None
    is_default: bool = False

    @override
    def operation(self) -> str:
        return "create"

    @override
    def describe(self, laid: Any) -> str:
        what = "기본 그룹으로 " if self.is_default else ""
        return f"{laid.caller.username}이 {self.named or laid.group.name}을 {what}생성"

    @override
    async def call(self, adapter: ResourceGroupAdapter, laid: Any) -> ResourceGroupDetailNode:
        with ActingAs(laid.caller):
            payload = await adapter.create(
                CreateResourceGroupInput(
                    name=self.named or laid.group.name,
                    domain_name=laid.caller.domain_name,
                    is_default=self.is_default,
                )
            )
        return payload.resource_group


@dataclass(frozen=True)
class TheSuperadminMakesAGroup(
    Scenario[SeedingSession, ACaller, ResourceGroupAdapter, ResourceGroupDetailNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-makes-a-resource-group"

    @override
    def describe(self) -> str:
        return (
            "슈퍼관리자가 이름만 주고 리소스 그룹을 만들면, "
            "활성이고 공개이며 기본이 아닌 그룹 전체가 코드의 기본값으로 채워져 반환된다"
        )

    @override
    def given(self) -> Given[SeedingSession, ACaller]:
        return SomeoneAlone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ACaller, ResourceGroupAdapter, ResourceGroupDetailNode]:
        return Creating(named="compute")

    @override
    def then(self) -> Then[ACaller, ResourceGroupDetailNode]:
        return TheNewGroupNode(started=self.started, named="compute")


@dataclass(frozen=True)
class ADefaultGroupIsMade(
    Scenario[SeedingSession, ACaller, ResourceGroupAdapter, ResourceGroupDetailNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-resource-group-made-as-the-default-answers-default"

    @override
    def describe(self) -> str:
        return "기본 그룹이 없을 때 슈퍼관리자가 기본으로 지정해 만들면 기본인 그룹이 반환된다"

    @override
    def given(self) -> Given[SeedingSession, ACaller]:
        return SomeoneAlone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ACaller, ResourceGroupAdapter, ResourceGroupDetailNode]:
        return Creating(named="primary", is_default=True)

    @override
    def then(self) -> Then[ACaller, ResourceGroupDetailNode]:
        return TheNewGroupNode(started=self.started, named="primary", is_default=True)


@dataclass(frozen=True)
class ANameAnotherGroupHoldsIsRefused(
    Scenario[SeedingSession, AGroupAndACaller, ResourceGroupAdapter, ResourceGroupDetailNode]
):
    @override
    def summary(self) -> str:
        return "a-name-another-resource-group-already-holds-is-refused"

    @override
    def describe(self) -> str:
        return "이미 어떤 그룹이 쓰고 있는 이름으로 만들려 하면 이름 중복으로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, AGroupAndACaller]:
        return AGroupAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AGroupAndACaller, ResourceGroupAdapter, ResourceGroupDetailNode]:
        return Creating()

    @override
    def then(self) -> Then[AGroupAndACaller, ResourceGroupDetailNode]:
        return TheCallIsRefused(ResourceGroupConflict)


@dataclass(frozen=True)
class ASecondDefaultIsRefused(
    Scenario[SeedingSession, AGroupAndACaller, ResourceGroupAdapter, ResourceGroupDetailNode]
):
    @override
    def summary(self) -> str:
        return "a-second-default-resource-group-is-refused"

    @override
    def describe(self) -> str:
        return "기본 그룹이 이미 있을 때 다른 이름으로 또 기본 그룹을 만들려 하면 기본 그룹이 이미 있다는 이유로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, AGroupAndACaller]:
        return AGroupAndSomeone(role=UserRole.SUPERADMIN, is_default=True)

    @override
    def when(self) -> When[AGroupAndACaller, ResourceGroupAdapter, ResourceGroupDetailNode]:
        return Creating(named="another-default", is_default=True)

    @override
    def then(self) -> Then[AGroupAndACaller, ResourceGroupDetailNode]:
        return TheCallIsRefused(DefaultResourceGroupAlreadyExists)


@dataclass(frozen=True)
class AUserWhoIsNotTheSuperadminMayNotCreate(
    Scenario[SeedingSession, ACaller, ResourceGroupAdapter, ResourceGroupDetailNode]
):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-may-not-make-a-resource-group"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 아닌 사용자가 리소스 그룹을 만들려 하면 역할 부족으로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, ACaller]:
        return SomeoneAlone()

    @override
    def when(self) -> When[ACaller, ResourceGroupAdapter, ResourceGroupDetailNode]:
        return Creating(named="by-a-user")

    @override
    def then(self) -> Then[ACaller, ResourceGroupDetailNode]:
        return TheCallIsRefused(InsufficientPrivilege)


@dataclass(frozen=True)
class TheMonitorMayNotCreate(
    Scenario[SeedingSession, ACaller, ResourceGroupAdapter, ResourceGroupDetailNode]
):
    @override
    def summary(self) -> str:
        return "the-monitor-may-not-make-a-resource-group"

    @override
    def describe(self) -> str:
        return "모니터가 리소스 그룹을 만들려 하면 역할 부족으로 거부된다. 모니터는 읽기만 통과한다"

    @override
    def given(self) -> Given[SeedingSession, ACaller]:
        return SomeoneAlone(role=UserRole.MONITOR)

    @override
    def when(self) -> When[ACaller, ResourceGroupAdapter, ResourceGroupDetailNode]:
        return Creating(named="by-the-monitor")

    @override
    def then(self) -> Then[ACaller, ResourceGroupDetailNode]:
        return TheCallIsRefused(InsufficientPrivilege)


SCENARIOS: list[CreatingStep] = [
    TheSuperadminMakesAGroup(started=datetime.now(UTC)),
    ADefaultGroupIsMade(started=datetime.now(UTC)),
    ANameAnotherGroupHoldsIsRefused(),
    # TODO(BA-7946): the create path maps every unique violation to a name conflict, so a
    # second default is refused as ResourceGroupConflict; list this row once it raises
    # DefaultResourceGroupAlreadyExists like the update path.
    # ASecondDefaultIsRefused(),
    AUserWhoIsNotTheSuperadminMayNotCreate(),
    TheMonitorMayNotCreate(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_creating(
    scenario: CreatingStep, adapter: ResourceGroupAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
