"""도메인과 레지스트리 relation 지우기 — 두 스코프의 권한과 없는 relation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override
from uuid import UUID

import pytest
import sqlalchemy as sa

from ai.backend.common.dto.manager.v2.domain.request import (
    PurgeDomainContainerRegistryRelationsInput,
)
from ai.backend.common.dto.manager.v2.domain.response import (
    PurgeDomainContainerRegistryRelationsPayload,
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
type Purged = PurgeDomainContainerRegistryRelationsPayload
type UnrelateScenario = Scenario[TestSeedingSession, Laid, DomainAdapter, Purged]


@dataclass(frozen=True)
class Unrelating(When[Laid, DomainAdapter, Purged]):
    @override
    def operation(self) -> str:
        return "purge_container_registry_relations"

    @override
    def describe(self, laid: Laid) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.domain.name}와 그 레지스트리 사이의 relation을 지웁니다",
            english=(
                f"{laid.caller.username} removes the relation between {laid.domain.name} "
                f"and that registry"
            ),
        )

    @override
    async def call(self, adapter: DomainAdapter, laid: Laid) -> Purged:
        with ActingAs(laid.caller):
            return await adapter.purge_container_registry_relations(
                PurgeDomainContainerRegistryRelationsInput(
                    domain_id=laid.domain.id, container_registry_ids=[laid.registry.id]
                )
            )


@dataclass(frozen=True)
class TheUnrelatedRegistriesComeBack(Then[Laid, Purged]):
    """이번 요청이 relation을 지운 레지스트리만 응답에 온다."""

    was_related: bool

    @override
    def says(self) -> str:
        if self.was_related:
            return Says(
                "도메인 id와 relation을 지운 레지스트리의 id가 옵니다",
                english="the domain id and the id of the unrelated registry come back",
            )
        return Says(
            "도메인 id와 빈 레지스트리 목록이 옵니다",
            english="the domain id and an empty registry list come back",
        )

    @override
    def look(self, laid: Laid, answered: Answered[Purged]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        registry_ids: list[Verdict] = [
            Same[list[UUID]]("container_registry_ids", payload.container_registry_ids, [])
        ]
        if self.was_related:
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
class AUserGrantedOnBothScopesUnrelates(Scenario[TestSeedingSession, Laid, DomainAdapter, Purged]):
    @override
    def summary(self) -> str:
        return "a-user-granted-on-both-scopes-unrelates-a-domain-from-a-registry"

    @override
    def describe(self) -> str:
        return Says(
            "도메인과 레지스트리 두 스코프 모두에 권한을 받은 사용자는 둘 사이의 relation을 지울 수 있습니다",
            english=(
                "a user granted permission on both the domain and the registry scopes can "
                "remove the relation between the two"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, Laid]:
        return ADomainAndARegistryToRelate(related=True)

    @override
    def when(self) -> When[Laid, DomainAdapter, Purged]:
        return Unrelating()

    @override
    def then(self) -> Then[Laid, Purged]:
        return TheUnrelatedRegistriesComeBack(was_related=True)


@dataclass(frozen=True)
class AUserGrantedOnTheRegistryAloneMayNotUnrelate(
    Scenario[TestSeedingSession, Laid, DomainAdapter, Purged]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-on-the-registry-alone-may-not-unrelate-it-from-a-domain"

    @override
    def describe(self) -> str:
        return Says(
            "레지스트리에만 권한을 받은 사용자가 도메인과의 relation을 지우려 하면 거부됩니다",
            english=(
                "a user granted permission on the registry alone is refused when removing "
                "its relation to a domain"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, Laid]:
        return ADomainAndARegistryToRelate(on_domain=False, related=True)

    @override
    def when(self) -> When[Laid, DomainAdapter, Purged]:
        return Unrelating()

    @override
    def then(self) -> Then[Laid, Any]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class UnrelatingAPairNotRelatedLeavesItOut(
    Scenario[TestSeedingSession, Laid, DomainAdapter, Purged]
):
    @override
    def summary(self) -> str:
        return "unrelating-a-registry-not-related-leaves-it-out-of-the-response"

    @override
    def describe(self) -> str:
        return Says(
            "relation이 없는 레지스트리를 요청해도 거부되지 않고, 응답에서는 빠집니다",
            english=(
                "requesting a registry not related to the domain is not refused, and the "
                "registry is left out of the response"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, Laid]:
        return ADomainAndARegistryToRelate()

    @override
    def when(self) -> When[Laid, DomainAdapter, Purged]:
        return Unrelating()

    @override
    def then(self) -> Then[Laid, Purged]:
        return TheUnrelatedRegistriesComeBack(was_related=False)


SCENARIOS: list[UnrelateScenario] = [
    AUserGrantedOnBothScopesUnrelates(),
    AUserGrantedOnTheRegistryAloneMayNotUnrelate(),
    UnrelatingAPairNotRelatedLeavesItOut(),
]


def expected_relation_count(scenario: UnrelateScenario) -> int:
    match scenario:
        case AUserGrantedOnTheRegistryAloneMayNotUnrelate():
            return 1
        case _:
            return 0


async def relation_count(engine: ExtendedAsyncSAEngine) -> int:
    async with engine.begin_readonly_session() as session:
        query = sa.select(sa.func.count()).select_from(DomainContainerRegistryRelationRow)
        return int(await session.scalar(query) or 0)


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_unrelating_registries(
    scenario: UnrelateScenario, adapter: DomainAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
    assert await relation_count(engine) == expected_relation_count(scenario)
