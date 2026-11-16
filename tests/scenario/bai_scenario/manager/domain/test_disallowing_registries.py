"""도메인에서 레지스트리 허용 거두기 — 두 스코프의 권한과 허용되지 않은 레지스트리."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override
from uuid import UUID

import pytest
import sqlalchemy as sa

from ai.backend.common.dto.manager.v2.domain.request import (
    DisallowDomainContainerRegistriesInput,
)
from ai.backend.common.dto.manager.v2.domain.response import (
    DisallowDomainContainerRegistriesPayload,
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
type Disallowed = DisallowDomainContainerRegistriesPayload
type DisallowScenario = Scenario[TestSeedingSession, Laid, DomainAdapter, Disallowed]


@dataclass(frozen=True)
class Disallowing(When[Laid, DomainAdapter, Disallowed]):
    @override
    def operation(self) -> str:
        return "disallow_container_registries"

    @override
    def describe(self, laid: Laid) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.domain.name}에서 그 레지스트리의 허용을 거둡니다",
            english=f"{laid.caller.username} disallows that registry for {laid.domain.name}",
        )

    @override
    async def call(self, adapter: DomainAdapter, laid: Laid) -> Disallowed:
        with ActingAs(laid.caller):
            return await adapter.disallow_container_registries(
                DisallowDomainContainerRegistriesInput(
                    domain_id=laid.domain.id, container_registry_ids=[laid.registry.id]
                )
            )


@dataclass(frozen=True)
class TheDisallowedRegistriesComeBack(Then[Laid, Disallowed]):
    """이번 요청이 허용을 거둔 레지스트리만 응답에 온다."""

    was_allowed: bool

    @override
    def says(self) -> str:
        if self.was_allowed:
            return Says(
                "도메인 id와 허용을 거둔 레지스트리의 id가 옵니다",
                english="the domain id and the id of the disallowed registry come back",
            )
        return Says(
            "도메인 id와 빈 레지스트리 목록이 옵니다",
            english="the domain id and an empty registry list come back",
        )

    @override
    def look(self, laid: Laid, answered: Answered[Disallowed]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        registry_ids: list[Verdict] = [
            Same[list[UUID]]("container_registry_ids", payload.container_registry_ids, [])
        ]
        if self.was_allowed:
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
class AUserGrantedOnBothScopesDisallows(
    Scenario[TestSeedingSession, Laid, DomainAdapter, Disallowed]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-on-both-scopes-disallows-a-registry-for-a-domain"

    @override
    def describe(self) -> str:
        return Says(
            "도메인과 레지스트리 두 스코프 모두에 권한을 받은 사용자는 도메인에서 그 레지스트리의 허용을 거둘 수 있습니다",
            english=(
                "a user granted permission on both the domain and the registry scopes can "
                "disallow the registry for the domain"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, Laid]:
        return ADomainAndARegistryToAllow(allowed=True)

    @override
    def when(self) -> When[Laid, DomainAdapter, Disallowed]:
        return Disallowing()

    @override
    def then(self) -> Then[Laid, Disallowed]:
        return TheDisallowedRegistriesComeBack(was_allowed=True)


@dataclass(frozen=True)
class AUserGrantedOnTheRegistryAloneMayNotDisallow(
    Scenario[TestSeedingSession, Laid, DomainAdapter, Disallowed]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-on-the-registry-alone-may-not-disallow-it-for-a-domain"

    @override
    def describe(self) -> str:
        return Says(
            "레지스트리에만 권한을 받은 사용자가 도메인에서 그 레지스트리의 허용을 거두려 하면 거부됩니다",
            english=(
                "a user granted permission on the registry alone is refused when disallowing "
                "it for a domain"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, Laid]:
        return ADomainAndARegistryToAllow(on_domain=False, allowed=True)

    @override
    def when(self) -> When[Laid, DomainAdapter, Disallowed]:
        return Disallowing()

    @override
    def then(self) -> Then[Laid, Any]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class DisallowingARegistryNotAllowedLeavesItOut(
    Scenario[TestSeedingSession, Laid, DomainAdapter, Disallowed]
):
    @override
    def summary(self) -> str:
        return "disallowing-a-registry-not-allowed-leaves-it-out-of-the-response"

    @override
    def describe(self) -> str:
        return Says(
            "허용되지 않은 레지스트리의 허용을 거둬도 거부되지 않고, 응답에서는 빠집니다",
            english=(
                "disallowing a registry the domain does not allow is not refused, and the "
                "registry is left out of the response"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, Laid]:
        return ADomainAndARegistryToAllow()

    @override
    def when(self) -> When[Laid, DomainAdapter, Disallowed]:
        return Disallowing()

    @override
    def then(self) -> Then[Laid, Disallowed]:
        return TheDisallowedRegistriesComeBack(was_allowed=False)


SCENARIOS: list[DisallowScenario] = [
    AUserGrantedOnBothScopesDisallows(),
    AUserGrantedOnTheRegistryAloneMayNotDisallow(),
    DisallowingARegistryNotAllowedLeavesItOut(),
]


def expected_relation_count(scenario: DisallowScenario) -> int:
    match scenario:
        case AUserGrantedOnTheRegistryAloneMayNotDisallow():
            return 1
        case _:
            return 0


async def relation_count(engine: ExtendedAsyncSAEngine) -> int:
    async with engine.begin_readonly_session() as session:
        query = sa.select(sa.func.count()).select_from(DomainContainerRegistryRelationRow)
        return int(await session.scalar(query) or 0)


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_disallowing_registries(
    scenario: DisallowScenario, adapter: DomainAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
    assert await relation_count(engine) == expected_relation_count(scenario)
