"""도메인에서 레지스트리 unlink하기 — 두 스코프의 권한과 link되지 않은 레지스트리."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import pytest
import sqlalchemy as sa

from ai.backend.common.dto.manager.v2.domain.request import (
    DomainContainerRegistryLinkInput,
    UnlinkDomainContainerRegistriesInput,
)
from ai.backend.common.dto.manager.v2.domain.response import (
    DomainContainerRegistryLink,
    UnlinkDomainContainerRegistriesPayload,
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
type Unlinked = UnlinkDomainContainerRegistriesPayload
type UnlinkScenario = Scenario[TestSeedingSession, Laid, DomainAdapter, Unlinked]


@dataclass(frozen=True)
class Unlinking(When[Laid, DomainAdapter, Unlinked]):
    @override
    def operation(self) -> str:
        return "unlink_container_registries"

    @override
    def describe(self, laid: Laid) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.domain.name}에서 그 레지스트리를 unlink합니다",
            english=f"{laid.caller.username} unlinks that registry from {laid.domain.name}",
        )

    @override
    async def call(self, adapter: DomainAdapter, laid: Laid) -> Unlinked:
        with ActingAs(laid.caller):
            return await adapter.unlink_container_registries(
                UnlinkDomainContainerRegistriesInput(
                    items=[
                        DomainContainerRegistryLinkInput(
                            domain_id=laid.domain.id, container_registry_id=laid.registry.id
                        )
                    ]
                )
            )


@dataclass(frozen=True)
class TheUnlinkedPairsComeBack(Then[Laid, Unlinked]):
    """이번 요청이 unlink한 쌍만 응답에 온다."""

    was_linked: bool

    @override
    def says(self) -> str:
        if self.was_linked:
            return Says(
                "unlink한 도메인과 레지스트리 한 쌍이 옵니다",
                english="the unlinked domain and registry pair comes back",
            )
        return Says("빈 목록이 옵니다", english="an empty list comes back")

    @override
    def look(self, laid: Laid, answered: Answered[Unlinked]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        if not self.was_linked:
            return [Same[list[DomainContainerRegistryLink]]("items", payload.items, [])]
        requested = DomainContainerRegistryLink(
            domain_id=laid.domain.id, container_registry_id=laid.registry.id
        )
        return [
            Held[list[DomainContainerRegistryLink]](
                "items",
                payload.items,
                SameAs(
                    [requested],
                    Says(
                        "요청한 도메인과 레지스트리 한 쌍",
                        english="the requested domain and registry pair",
                    ),
                ),
            )
        ]


@dataclass(frozen=True)
class AUserGrantedOnBothScopesUnlinks(Scenario[TestSeedingSession, Laid, DomainAdapter, Unlinked]):
    @override
    def summary(self) -> str:
        return "a-user-granted-on-both-scopes-unlinks-a-registry-from-a-domain"

    @override
    def describe(self) -> str:
        return Says(
            "도메인과 레지스트리 두 스코프 모두에 권한을 받은 사용자는 도메인에서 그 레지스트리를 unlink할 수 있습니다",
            english=(
                "a user granted permission on both the domain and the registry scopes can "
                "unlink the registry from the domain"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, Laid]:
        return ADomainAndARegistryToAllow(allowed=True)

    @override
    def when(self) -> When[Laid, DomainAdapter, Unlinked]:
        return Unlinking()

    @override
    def then(self) -> Then[Laid, Unlinked]:
        return TheUnlinkedPairsComeBack(was_linked=True)


@dataclass(frozen=True)
class AUserGrantedOnTheRegistryAloneMayNotUnlink(
    Scenario[TestSeedingSession, Laid, DomainAdapter, Unlinked]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-on-the-registry-alone-may-not-unlink-it-from-a-domain"

    @override
    def describe(self) -> str:
        return Says(
            "레지스트리에만 권한을 받은 사용자가 도메인에서 그 레지스트리를 unlink하려 하면 거부됩니다",
            english=(
                "a user granted permission on the registry alone is refused when unlinking "
                "it from a domain"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, Laid]:
        return ADomainAndARegistryToAllow(on_domain=False, allowed=True)

    @override
    def when(self) -> When[Laid, DomainAdapter, Unlinked]:
        return Unlinking()

    @override
    def then(self) -> Then[Laid, Any]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class UnlinkingARegistryNotLinkedLeavesItOut(
    Scenario[TestSeedingSession, Laid, DomainAdapter, Unlinked]
):
    @override
    def summary(self) -> str:
        return "unlinking-a-registry-not-linked-leaves-it-out-of-the-response"

    @override
    def describe(self) -> str:
        return Says(
            "link되지 않은 레지스트리를 unlink해도 거부되지 않고, 응답에서는 빠집니다",
            english=(
                "unlinking a registry not linked to the domain is not refused, and the "
                "pair is left out of the response"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, Laid]:
        return ADomainAndARegistryToAllow()

    @override
    def when(self) -> When[Laid, DomainAdapter, Unlinked]:
        return Unlinking()

    @override
    def then(self) -> Then[Laid, Unlinked]:
        return TheUnlinkedPairsComeBack(was_linked=False)


SCENARIOS: list[UnlinkScenario] = [
    AUserGrantedOnBothScopesUnlinks(),
    AUserGrantedOnTheRegistryAloneMayNotUnlink(),
    UnlinkingARegistryNotLinkedLeavesItOut(),
]


def expected_relation_count(scenario: UnlinkScenario) -> int:
    match scenario:
        case AUserGrantedOnTheRegistryAloneMayNotUnlink():
            return 1
        case _:
            return 0


async def relation_count(engine: ExtendedAsyncSAEngine) -> int:
    async with engine.begin_readonly_session() as session:
        query = sa.select(sa.func.count()).select_from(DomainContainerRegistryRelationRow)
        return int(await session.scalar(query) or 0)


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_unlinking_registries(
    scenario: UnlinkScenario, adapter: DomainAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
    assert await relation_count(engine) == expected_relation_count(scenario)
