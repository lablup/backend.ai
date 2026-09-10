"""리소스 그룹 만들기와 읽기."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, override

import pytest
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.domain import WAS_HERE, SomeoneOf, WrittenByThisRun
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario
from bai_scenario.seeds.domain.domain import SeedDomain
from bai_scenario.seeds.resource_group.resource_group import SeedResourceGroup

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.resource_group.request import CreateResourceGroupInput
from ai.backend.common.dto.manager.v2.resource_group.response import (
    ResourceGroupDetailNode,
)
from ai.backend.manager.api.adapters.resource_group.adapter import ResourceGroupAdapter
from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.data.resource_group.types import ResourceGroupData
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    Refused,
    Same,
    Scenario,
    Skipped,
    Then,
    Verdict,
    When,
)

MADE = "compute"
SCHEDULER = "fifo"


@dataclass(frozen=True)
class ADomainAndACaller:
    """리소스 그룹을 걸 도메인과, 부를 사람."""

    domain: DomainData
    caller: UserData


@dataclass(frozen=True)
class AGroupAndACaller:
    """이미 있는 리소스 그룹과, 부를 사람."""

    group: ResourceGroupData
    caller: UserData


@dataclass(frozen=True)
class ADomainAndSomeone(Given[Any, ADomainAndACaller]):
    """도메인 하나와, 그 도메인에 속한 사용자 한 명."""

    role: UserRole = UserRole.USER

    @override
    def describe(self) -> str:
        return f"도메인 하나와, 그 도메인에 속한 {self.role.value} 한 명"

    @override
    async def lay(self, seeding: Any) -> ADomainAndACaller:
        domain = await seeding.creating(SeedDomain(name_hint="home", description=WAS_HERE))
        caller = await seeding.within(SomeoneOf(domain, role=self.role))
        return ADomainAndACaller(seeding.made(domain), seeding.made(caller))


@dataclass(frozen=True)
class AGroupAndSomeone(Given[Any, AGroupAndACaller]):
    """이미 심어둔 리소스 그룹과, 그것을 읽을 사람 한 명."""

    role: UserRole = UserRole.SUPERADMIN

    @override
    def describe(self) -> str:
        return f"이미 있는 리소스 그룹과, {self.role.value} 한 명"

    @override
    async def lay(self, seeding: Any) -> AGroupAndACaller:
        domain = await seeding.creating(SeedDomain(name_hint="home", description=WAS_HERE))
        group = await seeding.creating(SeedResourceGroup(name_hint=MADE, scheduler=SCHEDULER))
        caller = await seeding.within(SomeoneOf(domain, role=self.role))
        return AGroupAndACaller(seeding.made(group), seeding.made(caller))


@dataclass(frozen=True)
class MakingAGroup(When[ADomainAndACaller, ResourceGroupAdapter, ResourceGroupDetailNode]):
    """그 도메인 아래에 리소스 그룹을 만든다."""

    named: str = MADE

    @override
    def operation(self) -> str:
        return "create"

    @override
    def describe(self, laid: ADomainAndACaller) -> str:
        return f"{laid.caller.username}이 {laid.domain.name} 아래에 {self.named}을 만듦"

    @override
    async def call(
        self, adapter: ResourceGroupAdapter, laid: ADomainAndACaller
    ) -> ResourceGroupDetailNode:
        with ActingAs(laid.caller):
            payload = await adapter.create(
                CreateResourceGroupInput(name=self.named, domain_name=laid.domain.name)
            )
        return payload.resource_group


@dataclass(frozen=True)
class ReadingAGroupByName(When[AGroupAndACaller, ResourceGroupAdapter, ResourceGroupDetailNode]):
    """심은 리소스 그룹을 이름으로 읽는다."""

    @override
    def operation(self) -> str:
        return "get"

    @override
    def describe(self, laid: AGroupAndACaller) -> str:
        return f"{laid.caller.username}이 {laid.group.name}으로 조회"

    @override
    async def call(
        self, adapter: ResourceGroupAdapter, laid: AGroupAndACaller
    ) -> ResourceGroupDetailNode:
        with ActingAs(laid.caller):
            return await adapter.get(laid.group.name)


@dataclass(frozen=True)
class TheGroupComesBack(Then[Any, ResourceGroupDetailNode]):
    """리소스 그룹이 통째로 온다."""

    started: datetime
    named: str

    @override
    def says(self) -> str:
        return "리소스 그룹 전체가 온다"

    @override
    def look(self, laid: Any, answered: Answered[ResourceGroupDetailNode]) -> list[Verdict]:
        node = answered.response
        if node is None:
            return [Refused(InsufficientPrivilege, answered.raised)]
        return [
            Same("name", node.name, self.named),
            Same("status.is_active", node.status.is_active, True),
            Same("status.is_public", node.status.is_public, True),
            Same("status.is_default", node.status.is_default, False),
            Same("metadata.description", node.metadata.description, None),
            Same("network.wsproxy_addr", node.network.wsproxy_addr, None),
            Same("network.use_host_network", node.network.use_host_network, False),
            Skipped("id", "데이터베이스가 만든다"),
            Skipped("scheduler", "설치본이 정한 기본값이라 시나리오가 말할 수 없다"),
            Skipped("default_deployment_options", "설치본이 정한 기본값이다"),
            Skipped("default_session_options", "설치본이 정한 기본값이다"),
            Held("metadata.created_at", node.metadata.created_at, WrittenByThisRun(self.started)),
        ]


@dataclass(frozen=True)
class TheSuperadminMakesAGroup(
    Scenario[SeedingSession, ADomainAndACaller, ResourceGroupAdapter, ResourceGroupDetailNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-makes-a-resource-group-in-a-domain"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 도메인 아래에 리소스 그룹을 만들면, 그 이름의 그룹이 답으로 온다"

    @override
    def given(self) -> Given[SeedingSession, ADomainAndACaller]:
        return ADomainAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(
        self,
    ) -> When[ADomainAndACaller, ResourceGroupAdapter, ResourceGroupDetailNode]:
        return MakingAGroup()

    @override
    def then(self) -> Then[ADomainAndACaller, ResourceGroupDetailNode]:
        return TheGroupComesBack(started=self.started, named=MADE)


@dataclass(frozen=True)
class APlainUserMayNotMakeAGroup(
    Scenario[SeedingSession, ADomainAndACaller, ResourceGroupAdapter, ResourceGroupDetailNode]
):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-may-not-make-a-resource-group"

    @override
    def describe(self) -> str:
        return (
            "리소스 그룹 생성은 도메인 생성과 같이 전역 역할이 지키므로, "
            "슈퍼관리자가 아닌 사용자는 권한을 얼마나 받았는지와 무관하게 막힌다"
        )

    @override
    def given(self) -> Given[SeedingSession, ADomainAndACaller]:
        return ADomainAndSomeone()

    @override
    def when(
        self,
    ) -> When[ADomainAndACaller, ResourceGroupAdapter, ResourceGroupDetailNode]:
        return MakingAGroup(named="refused")

    @override
    def then(self) -> Then[ADomainAndACaller, ResourceGroupDetailNode]:
        return TheCallIsRefused(InsufficientPrivilege)


@dataclass(frozen=True)
class AGroupAlreadyThereIsReadBack(
    Scenario[SeedingSession, AGroupAndACaller, ResourceGroupAdapter, ResourceGroupDetailNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-resource-group-already-there-is-read-back-by-name"

    @override
    def describe(self) -> str:
        return "리소스 그룹이 이미 있을 때 이름으로 조회하면, 그 그룹이 답으로 온다"

    @override
    def given(self) -> Given[SeedingSession, AGroupAndACaller]:
        return AGroupAndSomeone()

    @override
    def when(
        self,
    ) -> When[AGroupAndACaller, ResourceGroupAdapter, ResourceGroupDetailNode]:
        return ReadingAGroupByName()

    @override
    def then(self) -> Then[AGroupAndACaller, ResourceGroupDetailNode]:
        return TheGroupComesBack(started=self.started, named=f"{MADE}-1")


SCENARIOS: list[Scenario[SeedingSession, Any, ResourceGroupAdapter, ResourceGroupDetailNode]] = [
    TheSuperadminMakesAGroup(started=datetime.now(UTC)),
    APlainUserMayNotMakeAGroup(),
    AGroupAlreadyThereIsReadBack(started=datetime.now(UTC)),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_resource_group(
    scenario: Scenario[SeedingSession, Any, ResourceGroupAdapter, ResourceGroupDetailNode],
    adapter: ResourceGroupAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
