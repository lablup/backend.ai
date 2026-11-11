"""도메인과 레지스트리 relation 맞추기 — 레지스트리 id 목록에 맞춰 relation이 생기고 지워지는가."""

from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import Any, override

import pytest
import sqlalchemy as sa

from ai.backend.common.data.entity.container_registry import ContainerRegistryID
from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.user.types import UserRole
from ai.backend.manager.api.adapters.domain.adapter import DomainAdapter
from ai.backend.manager.data.container_registry.types import ContainerRegistryData
from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.domain_container_registry_relation.row import (
    DomainContainerRegistryRelationRow,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Same,
    Says,
    Scenario,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.domain import SomeoneOf, TheCallIsRefused
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario
from bai_scenario.seeds.domain.domain import TestSeedDomain
from bai_scenario.seeds.image.registry import AllowDomain, TestSeedContainerRegistry


@dataclass(frozen=True)
class ADomainARegistryAndACaller:
    domain: DomainData
    registry: ContainerRegistryData
    caller: UserData


@dataclass(frozen=True)
class ADomainARegistryAndSomeone(Given[TestSeedingSession, ADomainARegistryAndACaller]):
    """도메인 하나, 레지스트리 하나, 그 도메인에 속한 사용자 한 명."""

    role: UserRole = UserRole.SUPERADMIN
    linked: bool = False

    @override
    def describe(self) -> str:
        if self.linked:
            return Says(
                f"도메인 하나와 레지스트리 하나, 둘 사이에 relation이 이미 있고, "
                f"그 도메인에 속한 {self.role.value} 한 명이 있습니다",
                english=(
                    f"one domain and one registry already related to each other, "
                    f"and one {self.role.value} in that domain"
                ),
            )
        return Says(
            f"도메인 하나와 레지스트리 하나, 그 도메인에 속한 {self.role.value} 한 명이 있습니다",
            english=f"one domain, one registry, and one {self.role.value} in that domain",
        )

    @override
    async def lay(self, seeding: TestSeedingSession) -> ADomainARegistryAndACaller:
        domain = await seeding.creating(TestSeedDomain(name_hint="allowing"))
        registry = await seeding.creating(TestSeedContainerRegistry(name_hint="allowed"))
        if self.linked:
            await seeding.linking(AllowDomain(), domain, registry)
        caller = await seeding.within(SomeoneOf(domain, role=self.role))
        return ADomainARegistryAndACaller(
            domain=seeding.made(domain),
            registry=seeding.made(registry),
            caller=seeding.made(caller),
        )


class RegistriesGiven(enum.Enum):
    """sync에 넘기는 레지스트리 id 목록."""

    THE_REGISTRY = Says("그 레지스트리", english="that registry")
    NOTHING = Says("빈 목록", english="an empty list")

    def of(self, laid: ADomainARegistryAndACaller) -> list[ContainerRegistryID]:
        match self:
            case RegistriesGiven.THE_REGISTRY:
                return [ContainerRegistryID(laid.registry.id)]
            case RegistriesGiven.NOTHING:
                return []


@dataclass(frozen=True)
class Syncing(When[ADomainARegistryAndACaller, DomainAdapter, None]):
    registries: RegistriesGiven

    @override
    def operation(self) -> str:
        return "sync_registry_relations"

    @override
    def describe(self, laid: ADomainARegistryAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.domain.name}의 relation을 "
            f"{self.registries.value}에 맞춥니다",
            english=(
                f"{laid.caller.username} syncs the relations of {laid.domain.name} "
                f"to {self.registries.value.english}"
            ),
        )

    @override
    async def call(self, adapter: DomainAdapter, laid: ADomainARegistryAndACaller) -> None:
        with ActingAs(laid.caller):
            await adapter.sync_registry_relations(
                DomainID(laid.domain.id), self.registries.of(laid)
            )


@dataclass(frozen=True)
class TheCallReturnsNothing(Then[ADomainARegistryAndACaller, None]):
    @override
    def says(self) -> str:
        return Says(
            "반환값이 없고 예외도 발생하지 않습니다",
            english="the call returns nothing and raises nothing",
        )

    @override
    def look(self, laid: ADomainARegistryAndACaller, answered: Answered[None]) -> list[Verdict]:
        if answered.raised is not None:
            return [Same("raised", answered.raised, None)]
        return [Same("response", answered.response, None)]


type SyncScenario = Scenario[TestSeedingSession, ADomainARegistryAndACaller, DomainAdapter, None]


@dataclass(frozen=True)
class GivingARegistryLinksIt(
    Scenario[TestSeedingSession, ADomainARegistryAndACaller, DomainAdapter, None]
):
    @override
    def summary(self) -> str:
        return "giving-a-registry-links-the-domain-to-it"

    @override
    def describe(self) -> str:
        return Says(
            "슈퍼관리자가 레지스트리를 넘겨 맞추면 도메인과 그 레지스트리 사이에 relation이 생깁니다",
            english=(
                "when the superadmin syncs with a registry, the domain and that registry "
                "become related"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ADomainARegistryAndACaller]:
        return ADomainARegistryAndSomeone()

    @override
    def when(self) -> When[ADomainARegistryAndACaller, DomainAdapter, None]:
        return Syncing(RegistriesGiven.THE_REGISTRY)

    @override
    def then(self) -> Then[ADomainARegistryAndACaller, None]:
        return TheCallReturnsNothing()


@dataclass(frozen=True)
class LeavingARegistryOutUnlinksIt(
    Scenario[TestSeedingSession, ADomainARegistryAndACaller, DomainAdapter, None]
):
    @override
    def summary(self) -> str:
        return "leaving-a-linked-registry-out-unlinks-it"

    @override
    def describe(self) -> str:
        return Says(
            "relation이 있는 레지스트리를 빼고 빈 목록으로 맞추면 그 relation이 지워집니다",
            english="syncing with an empty list removes the relation to a registry left out",
        )

    @override
    def given(self) -> Given[TestSeedingSession, ADomainARegistryAndACaller]:
        return ADomainARegistryAndSomeone(linked=True)

    @override
    def when(self) -> When[ADomainARegistryAndACaller, DomainAdapter, None]:
        return Syncing(RegistriesGiven.NOTHING)

    @override
    def then(self) -> Then[ADomainARegistryAndACaller, None]:
        return TheCallReturnsNothing()


@dataclass(frozen=True)
class AUserGrantedNothingMayNotSync(
    Scenario[TestSeedingSession, ADomainARegistryAndACaller, DomainAdapter, None]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-sync-registry-relations"

    @override
    def describe(self) -> str:
        return Says(
            "도메인에 아무 권한이 없는 사용자가 relation을 맞추려 하면 거부됩니다",
            english="a user granted nothing on the domain is refused when syncing the relations",
        )

    @override
    def given(self) -> Given[TestSeedingSession, ADomainARegistryAndACaller]:
        return ADomainARegistryAndSomeone(role=UserRole.USER)

    @override
    def when(self) -> When[ADomainARegistryAndACaller, DomainAdapter, None]:
        return Syncing(RegistriesGiven.THE_REGISTRY)

    @override
    def then(self) -> Then[ADomainARegistryAndACaller, Any]:
        return TheCallIsRefused(NotEnoughPermission)


SCENARIOS: list[SyncScenario] = [
    GivingARegistryLinksIt(),
    LeavingARegistryOutUnlinksIt(),
    AUserGrantedNothingMayNotSync(),
]


def expected_relation_count(scenario: SyncScenario) -> int:
    match scenario:
        case GivingARegistryLinksIt():
            return 1
        case _:
            return 0


async def relation_count(engine: ExtendedAsyncSAEngine) -> int:
    async with engine.begin_readonly_session() as session:
        query = sa.select(sa.func.count()).select_from(DomainContainerRegistryRelationRow)
        return int(await session.scalar(query) or 0)


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_syncing_registry_relations(
    scenario: SyncScenario, adapter: DomainAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
    assert await relation_count(engine) == expected_relation_count(scenario)
