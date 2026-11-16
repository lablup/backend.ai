"""도메인에 레지스트리 허용하기 — 두 스코프의 권한과 이미 허용된 레지스트리."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override
from uuid import UUID

import pytest
import sqlalchemy as sa

from ai.backend.common.dto.manager.v2.domain.request import (
    AllowDomainContainerRegistriesInput,
)
from ai.backend.common.dto.manager.v2.domain.response import (
    AllowDomainContainerRegistriesPayload,
)
from ai.backend.manager.api.adapters.domain.adapter import DomainAdapter
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.domain_container_registry_relation.row import (
    DomainContainerRegistryRelationRow,
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
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.container_registry import (
    ADomainAndARegistryToAllow,
    ADomainAndARegistryToAllowAndACaller,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Laid = ADomainAndARegistryToAllowAndACaller
type Allowed = AllowDomainContainerRegistriesPayload
type AllowScenario = Scenario[TestSeedingSession, Laid, DomainAdapter, Allowed]


@dataclass(frozen=True)
class Allowing(When[Laid, DomainAdapter, Allowed]):
    @override
    def operation(self) -> str:
        return "allow_container_registries"

    @override
    def describe(self, laid: Laid) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.domain.name}에 그 레지스트리를 허용합니다",
            english=f"{laid.caller.username} allows that registry for {laid.domain.name}",
        )

    @override
    async def call(self, adapter: DomainAdapter, laid: Laid) -> Allowed:
        with ActingAs(laid.caller):
            return await adapter.allow_container_registries(
                AllowDomainContainerRegistriesInput(
                    domain_id=laid.domain.id, container_registry_ids=[laid.registry.id]
                )
            )


@dataclass(frozen=True)
class TheAllowedRegistriesComeBack(Then[Laid, Allowed]):
    """이번 요청이 새로 허용한 레지스트리만 응답에 온다."""

    newly_allowed: bool

    @override
    def says(self) -> str:
        if self.newly_allowed:
            return Says(
                "도메인 id와 새로 허용한 레지스트리의 id가 옵니다",
                english="the domain id and the id of the newly allowed registry come back",
            )
        return Says(
            "도메인 id와 빈 레지스트리 목록이 옵니다",
            english="the domain id and an empty registry list come back",
        )

    @override
    def look(self, laid: Laid, answered: Answered[Allowed]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        registry_ids: list[Verdict] = [
            Same[list[UUID]]("container_registry_ids", payload.container_registry_ids, [])
        ]
        if self.newly_allowed:
            registry_ids = [
                Held[list[UUID]](
                    "container_registry_ids",
                    payload.container_registry_ids,
                    SameAs(
                        [laid.registry.id],
                        Says("요청한 레지스트리의 id 하나", english="the requested registry id"),
                    ),
                )
            ]
        return [
            Held[UUID](
                "domain_id",
                payload.domain_id,
                SameAs(
                    laid.domain.id, Says("요청한 도메인의 id", english="the requested domain id")
                ),
            ),
            *registry_ids,
        ]


@dataclass(frozen=True)
class AUserGrantedOnBothScopesAllows(Scenario[TestSeedingSession, Laid, DomainAdapter, Allowed]):
    @override
    def summary(self) -> str:
        return "a-user-granted-on-both-scopes-allows-a-registry-for-a-domain"

    @override
    def describe(self) -> str:
        return Says(
            "도메인과 레지스트리 두 스코프 모두에 권한을 받은 사용자는 도메인에 그 레지스트리를 허용할 수 있습니다",
            english=(
                "a user granted permission on both the domain and the registry scopes can "
                "allow the registry for the domain"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, Laid]:
        return ADomainAndARegistryToAllow()

    @override
    def when(self) -> When[Laid, DomainAdapter, Allowed]:
        return Allowing()

    @override
    def then(self) -> Then[Laid, Allowed]:
        return TheAllowedRegistriesComeBack(newly_allowed=True)


@dataclass(frozen=True)
class AUserGrantedOnTheRegistryAloneMayNotAllow(
    Scenario[TestSeedingSession, Laid, DomainAdapter, Allowed]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-on-the-registry-alone-may-not-allow-it-for-a-domain"

    @override
    def describe(self) -> str:
        return Says(
            "레지스트리에만 권한을 받은 사용자가 도메인에 그 레지스트리를 허용하려 하면 거부됩니다",
            english=(
                "a user granted permission on the registry alone is refused when allowing "
                "it for a domain"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, Laid]:
        return ADomainAndARegistryToAllow(on_domain=False)

    @override
    def when(self) -> When[Laid, DomainAdapter, Allowed]:
        return Allowing()

    @override
    def then(self) -> Then[Laid, Any]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AllowingAnAllowedRegistryLeavesItOut(
    Scenario[TestSeedingSession, Laid, DomainAdapter, Allowed]
):
    @override
    def summary(self) -> str:
        return "allowing-an-already-allowed-registry-leaves-it-out-of-the-response"

    @override
    def describe(self) -> str:
        return Says(
            "이미 허용된 레지스트리를 다시 허용해도 거부되지 않고, 응답에서는 빠집니다",
            english=(
                "allowing a registry the domain already allows is not refused, and the "
                "registry is left out of the response"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, Laid]:
        return ADomainAndARegistryToAllow(allowed=True)

    @override
    def when(self) -> When[Laid, DomainAdapter, Allowed]:
        return Allowing()

    @override
    def then(self) -> Then[Laid, Allowed]:
        return TheAllowedRegistriesComeBack(newly_allowed=False)


SCENARIOS: list[AllowScenario] = [
    AUserGrantedOnBothScopesAllows(),
    AUserGrantedOnTheRegistryAloneMayNotAllow(),
    AllowingAnAllowedRegistryLeavesItOut(),
]


def expected_relation_count(scenario: AllowScenario) -> int:
    match scenario:
        case AUserGrantedOnTheRegistryAloneMayNotAllow():
            return 0
        case _:
            return 1


async def relation_count(engine: ExtendedAsyncSAEngine) -> int:
    async with engine.begin_readonly_session() as session:
        query = sa.select(sa.func.count()).select_from(DomainContainerRegistryRelationRow)
        return int(await session.scalar(query) or 0)


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_allowing_registries(
    scenario: AllowScenario, adapter: DomainAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
    assert await relation_count(engine) == expected_relation_count(scenario)
