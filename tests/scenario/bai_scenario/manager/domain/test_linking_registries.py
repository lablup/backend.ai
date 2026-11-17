"""도메인에 레지스트리 link하기 — 두 스코프의 권한과 이미 link된 레지스트리."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import pytest
import sqlalchemy as sa

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.domain.request import (
    DomainContainerRegistryLinkInput,
    LinkDomainContainerRegistriesInput,
)
from ai.backend.common.dto.manager.v2.domain.response import (
    DomainContainerRegistryLink,
    LinkDomainContainerRegistriesPayload,
)
from ai.backend.manager.api.adapters.domain.adapter import DomainAdapter
from ai.backend.manager.errors.image import ContainerRegistryNotFound
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
    MISSING_ENTITY_ID,
    ADomainAndARegistryToAllow,
    ADomainAndARegistryToAllowAndACaller,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Laid = ADomainAndARegistryToAllowAndACaller
type Linked = LinkDomainContainerRegistriesPayload
type LinkScenario = Scenario[TestSeedingSession, Laid, DomainAdapter, Linked]


@dataclass(frozen=True)
class Linking(When[Laid, DomainAdapter, Linked]):
    missing_registry: bool = False

    @override
    def operation(self) -> str:
        return "link_container_registries"

    @override
    def describe(self, laid: Laid) -> str:
        if self.missing_registry:
            return Says(
                f"{laid.caller.username}이 {laid.domain.name}에 존재하지 않는 레지스트리를 link합니다",
                english=(
                    f"{laid.caller.username} links a registry that does not exist to "
                    f"{laid.domain.name}"
                ),
            )
        return Says(
            f"{laid.caller.username}이 {laid.domain.name}에 그 레지스트리를 link합니다",
            english=f"{laid.caller.username} links that registry to {laid.domain.name}",
        )

    @override
    async def call(self, adapter: DomainAdapter, laid: Laid) -> Linked:
        with ActingAs(laid.caller):
            return await adapter.link_container_registries(
                LinkDomainContainerRegistriesInput(
                    items=[
                        DomainContainerRegistryLinkInput(
                            domain_id=laid.domain.id,
                            container_registry_id=(
                                MISSING_ENTITY_ID if self.missing_registry else laid.registry.id
                            ),
                        )
                    ]
                )
            )


@dataclass(frozen=True)
class TheLinkedPairsComeBack(Then[Laid, Linked]):
    """이번 요청이 새로 link한 쌍만 응답에 온다."""

    newly_linked: bool

    @override
    def says(self) -> str:
        if self.newly_linked:
            return Says(
                "새로 link한 도메인과 레지스트리 한 쌍이 옵니다",
                english="the newly linked domain and registry pair comes back",
            )
        return Says("빈 목록이 옵니다", english="an empty list comes back")

    @override
    def look(self, laid: Laid, answered: Answered[Linked]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        if not self.newly_linked:
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
class AUserGrantedOnBothScopesLinks(Scenario[TestSeedingSession, Laid, DomainAdapter, Linked]):
    @override
    def summary(self) -> str:
        return "a-user-granted-on-both-scopes-links-a-registry-to-a-domain"

    @override
    def describe(self) -> str:
        return Says(
            "도메인과 레지스트리 두 스코프 모두에 권한을 받은 사용자는 도메인에 그 레지스트리를 link할 수 있습니다",
            english=(
                "a user granted permission on both the domain and the registry scopes can "
                "link the registry to the domain"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, Laid]:
        return ADomainAndARegistryToAllow()

    @override
    def when(self) -> When[Laid, DomainAdapter, Linked]:
        return Linking()

    @override
    def then(self) -> Then[Laid, Linked]:
        return TheLinkedPairsComeBack(newly_linked=True)


@dataclass(frozen=True)
class AUserGrantedOnTheRegistryAloneMayNotLink(
    Scenario[TestSeedingSession, Laid, DomainAdapter, Linked]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-on-the-registry-alone-may-not-link-it-to-a-domain"

    @override
    def describe(self) -> str:
        return Says(
            "레지스트리에만 권한을 받은 사용자가 도메인에 그 레지스트리를 link하려 하면 거부됩니다",
            english=(
                "a user granted permission on the registry alone is refused when linking "
                "it to a domain"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, Laid]:
        return ADomainAndARegistryToAllow(on_domain=False)

    @override
    def when(self) -> When[Laid, DomainAdapter, Linked]:
        return Linking()

    @override
    def then(self) -> Then[Laid, Any]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class LinkingALinkedRegistryLeavesItOut(Scenario[TestSeedingSession, Laid, DomainAdapter, Linked]):
    @override
    def summary(self) -> str:
        return "linking-an-already-linked-registry-leaves-it-out-of-the-response"

    @override
    def describe(self) -> str:
        return Says(
            "이미 link된 레지스트리를 다시 link해도 거부되지 않고, 응답에서는 빠집니다",
            english=(
                "linking a registry already linked to the domain is not refused, and the "
                "pair is left out of the response"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, Laid]:
        return ADomainAndARegistryToAllow(allowed=True)

    @override
    def when(self) -> When[Laid, DomainAdapter, Linked]:
        return Linking()

    @override
    def then(self) -> Then[Laid, Linked]:
        return TheLinkedPairsComeBack(newly_linked=False)


@dataclass(frozen=True)
class LinkingAMissingRegistryIsRefused(Scenario[TestSeedingSession, Laid, DomainAdapter, Linked]):
    @override
    def summary(self) -> str:
        return "a-superadmin-naming-a-registry-that-does-not-exist-is-refused"

    @override
    def describe(self) -> str:
        return Says(
            "존재하지 않는 레지스트리를 도메인에 link하려 하면 그 레지스트리가 없다는 이유로 "
            "거부됩니다",
            english=(
                "linking a registry that does not exist to a domain is refused because "
                "there is no such registry"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, Laid]:
        return ADomainAndARegistryToAllow(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[Laid, DomainAdapter, Linked]:
        return Linking(missing_registry=True)

    @override
    def then(self) -> Then[Laid, Any]:
        return TheCallIsRefused(ContainerRegistryNotFound)


SCENARIOS: list[LinkScenario] = [
    AUserGrantedOnBothScopesLinks(),
    AUserGrantedOnTheRegistryAloneMayNotLink(),
    LinkingALinkedRegistryLeavesItOut(),
    LinkingAMissingRegistryIsRefused(),
]


def expected_relation_count(scenario: LinkScenario) -> int:
    match scenario:
        case AUserGrantedOnTheRegistryAloneMayNotLink() | LinkingAMissingRegistryIsRefused():
            return 0
        case _:
            return 1


async def relation_count(engine: ExtendedAsyncSAEngine) -> int:
    async with engine.begin_readonly_session() as session:
        query = sa.select(sa.func.count()).select_from(DomainContainerRegistryRelationRow)
        return int(await session.scalar(query) or 0)


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_linking_registries(
    scenario: LinkScenario, adapter: DomainAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
    assert await relation_count(engine) == expected_relation_count(scenario)
