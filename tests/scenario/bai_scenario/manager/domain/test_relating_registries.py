"""도메인과 레지스트리 relation 만들기 — 두 스코프의 권한과 이미 있는 relation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override
from uuid import UUID

import pytest
import sqlalchemy as sa

from ai.backend.common.dto.manager.v2.domain.request import (
    CreateDomainContainerRegistryRelationsInput,
)
from ai.backend.common.dto.manager.v2.domain.response import (
    CreateDomainContainerRegistryRelationsPayload,
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
    ADomainAndARegistryToRelate,
    ADomainAndARegistryToRelateAndACaller,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Laid = ADomainAndARegistryToRelateAndACaller
type Created = CreateDomainContainerRegistryRelationsPayload
type RelateScenario = Scenario[TestSeedingSession, Laid, DomainAdapter, Created]


@dataclass(frozen=True)
class Relating(When[Laid, DomainAdapter, Created]):
    @override
    def operation(self) -> str:
        return "create_container_registry_relations"

    @override
    def describe(self, laid: Laid) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.domain.name}와 그 레지스트리 사이에 relation을 만듭니다",
            english=(f"{laid.caller.username} relates {laid.domain.name} to that registry"),
        )

    @override
    async def call(self, adapter: DomainAdapter, laid: Laid) -> Created:
        with ActingAs(laid.caller):
            return await adapter.create_container_registry_relations(
                CreateDomainContainerRegistryRelationsInput(
                    domain_id=laid.domain.id, container_registry_ids=[laid.registry.id]
                )
            )


@dataclass(frozen=True)
class TheRelatedRegistriesComeBack(Then[Laid, Created]):
    """이번 요청이 relation을 만든 레지스트리만 응답에 온다."""

    newly_related: bool

    @override
    def says(self) -> str:
        if self.newly_related:
            return Says(
                "도메인 id와 relation을 만든 레지스트리의 id가 옵니다",
                english="the domain id and the id of the newly related registry come back",
            )
        return Says(
            "도메인 id와 빈 레지스트리 목록이 옵니다",
            english="the domain id and an empty registry list come back",
        )

    @override
    def look(self, laid: Laid, answered: Answered[Created]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        registry_ids: list[Verdict] = [
            Same[list[UUID]]("container_registry_ids", payload.container_registry_ids, [])
        ]
        if self.newly_related:
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
class AUserGrantedOnBothScopesRelates(Scenario[TestSeedingSession, Laid, DomainAdapter, Created]):
    @override
    def summary(self) -> str:
        return "a-user-granted-on-both-scopes-relates-a-domain-to-a-registry"

    @override
    def describe(self) -> str:
        return Says(
            "도메인과 레지스트리 두 스코프 모두에 권한을 받은 사용자는 둘 사이에 relation을 만들 수 있습니다",
            english=(
                "a user granted permission on both the domain and the registry scopes can "
                "relate the two"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, Laid]:
        return ADomainAndARegistryToRelate()

    @override
    def when(self) -> When[Laid, DomainAdapter, Created]:
        return Relating()

    @override
    def then(self) -> Then[Laid, Created]:
        return TheRelatedRegistriesComeBack(newly_related=True)


@dataclass(frozen=True)
class AUserGrantedOnTheRegistryAloneMayNotRelate(
    Scenario[TestSeedingSession, Laid, DomainAdapter, Created]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-on-the-registry-alone-may-not-relate-it-to-a-domain"

    @override
    def describe(self) -> str:
        return Says(
            "레지스트리에만 권한을 받은 사용자가 도메인과 relation을 만들려 하면 거부됩니다",
            english=(
                "a user granted permission on the registry alone is refused when relating "
                "it to a domain"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, Laid]:
        return ADomainAndARegistryToRelate(on_domain=False)

    @override
    def when(self) -> When[Laid, DomainAdapter, Created]:
        return Relating()

    @override
    def then(self) -> Then[Laid, Any]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class RelatingAnAlreadyRelatedPairLeavesItOut(
    Scenario[TestSeedingSession, Laid, DomainAdapter, Created]
):
    @override
    def summary(self) -> str:
        return "relating-an-already-related-registry-leaves-it-out-of-the-response"

    @override
    def describe(self) -> str:
        return Says(
            "이미 relation이 있는 레지스트리를 다시 요청해도 거부되지 않고, 응답에서는 빠집니다",
            english=(
                "requesting a registry already related to the domain is not refused, and the "
                "registry is left out of the response"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, Laid]:
        return ADomainAndARegistryToRelate(related=True)

    @override
    def when(self) -> When[Laid, DomainAdapter, Created]:
        return Relating()

    @override
    def then(self) -> Then[Laid, Created]:
        return TheRelatedRegistriesComeBack(newly_related=False)


SCENARIOS: list[RelateScenario] = [
    AUserGrantedOnBothScopesRelates(),
    AUserGrantedOnTheRegistryAloneMayNotRelate(),
    RelatingAnAlreadyRelatedPairLeavesItOut(),
]


def expected_relation_count(scenario: RelateScenario) -> int:
    match scenario:
        case AUserGrantedOnTheRegistryAloneMayNotRelate():
            return 0
        case _:
            return 1


async def relation_count(engine: ExtendedAsyncSAEngine) -> int:
    async with engine.begin_readonly_session() as session:
        query = sa.select(sa.func.count()).select_from(DomainContainerRegistryRelationRow)
        return int(await session.scalar(query) or 0)


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_relating_registries(
    scenario: RelateScenario, adapter: DomainAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
    assert await relation_count(engine) == expected_relation_count(scenario)
