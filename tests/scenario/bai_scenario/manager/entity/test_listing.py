"""엔티티 유형 목록 조회 — 처리기 배선이 이름 붙인 유형을 이름순으로 돌려준다."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

import pytest

from ai.backend.common.data.entity.domain import DomainEntityType
from ai.backend.common.dto.manager.v2.entity.response import EntityTypeNode
from ai.backend.manager.api.adapters.entity.adapter import EntityAdapter
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
from bai_scenario.components.answers import MissingResponse
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type ListingStep = Scenario[TestSeedingSession, None, EntityAdapter, list[EntityTypeNode]]


@dataclass(frozen=True)
class DomainIsWired(Given[TestSeedingSession, None]):
    """adapter가 받는 배선은 conftest가 도메인 처리기 하나로 정한다. 심을 행은 없다."""

    @override
    def describe(self) -> str:
        return Says(
            "도메인 처리기가 배선되어 있습니다",
            english="the domain processors are wired",
        )

    @override
    async def lay(self, seeding: TestSeedingSession) -> None:
        return None


@dataclass(frozen=True)
class NothingIsWired(Given[TestSeedingSession, None]):
    """adapter가 받는 배선은 conftest가 비워 둔다. 심을 행은 없다."""

    @override
    def describe(self) -> str:
        return Says("배선된 처리기가 없습니다", english="no processors are wired")

    @override
    async def lay(self, seeding: TestSeedingSession) -> None:
        return None


@dataclass(frozen=True)
class Listing(When[None, EntityAdapter, list[EntityTypeNode]]):
    @override
    def operation(self) -> str:
        return "list_entity_types"

    @override
    def describe(self, laid: None) -> str:
        return Says("엔티티 유형 목록을 조회합니다", english="lists the entity types")

    @override
    async def call(self, adapter: EntityAdapter, laid: None) -> list[EntityTypeNode]:
        return adapter.list_entity_types().items


@dataclass(frozen=True)
class TheDomainIsListed(Then[None, list[EntityTypeNode]]):
    @override
    def says(self) -> str:
        return Says(
            "배선된 도메인 유형 하나가 그 이름으로 반환됩니다",
            english="the one wired domain type comes back by its name",
        )

    @override
    def look(self, laid: None, answered: Answered[list[EntityTypeNode]]) -> list[Verdict]:
        if answered.response is None:
            return [MissingResponse(answered.raised)]
        return [Same("items", answered.response, [EntityTypeNode(name=str(DomainEntityType()))])]


@dataclass(frozen=True)
class NothingIsListed(Then[None, list[EntityTypeNode]]):
    @override
    def says(self) -> str:
        return Says("빈 목록이 반환됩니다", english="an empty list comes back")

    @override
    def look(self, laid: None, answered: Answered[list[EntityTypeNode]]) -> list[Verdict]:
        if answered.response is None:
            return [MissingResponse(answered.raised)]
        return [Same("items", answered.response, [])]


@dataclass(frozen=True)
class TheWiredEntityTypeIsListed(
    Scenario[TestSeedingSession, None, EntityAdapter, list[EntityTypeNode]]
):
    @override
    def summary(self) -> str:
        return "the-wired-entity-type-is-listed"

    @override
    def describe(self) -> str:
        return Says(
            "처리기 배선이 이름 붙인 엔티티 유형이 반환됩니다",
            english="the entity type the processor wiring names comes back",
        )

    @override
    def given(self) -> Given[TestSeedingSession, None]:
        return DomainIsWired()

    @override
    def when(self) -> When[None, EntityAdapter, list[EntityTypeNode]]:
        return Listing()

    @override
    def then(self) -> Then[None, list[EntityTypeNode]]:
        return TheDomainIsListed()


@dataclass(frozen=True)
class NothingWiredListsNothing(
    Scenario[TestSeedingSession, None, EntityAdapter, list[EntityTypeNode]]
):
    @override
    def summary(self) -> str:
        return "nothing-wired-lists-nothing"

    @override
    def describe(self) -> str:
        return Says(
            "배선된 처리기가 없으면 빈 목록이 반환됩니다",
            english="when no processors are wired, an empty list comes back",
        )

    @override
    def given(self) -> Given[TestSeedingSession, None]:
        return NothingIsWired()

    @override
    def when(self) -> When[None, EntityAdapter, list[EntityTypeNode]]:
        return Listing()

    @override
    def then(self) -> Then[None, list[EntityTypeNode]]:
        return NothingIsListed()


@pytest.mark.parametrize(
    "scenario",
    [TheWiredEntityTypeIsListed()],
    ids=lambda scenario: scenario.summary(),
)
async def test_listing(
    scenario: ListingStep,
    adapter: EntityAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)


@pytest.mark.parametrize(
    "scenario",
    [NothingWiredListsNothing()],
    ids=lambda scenario: scenario.summary(),
)
async def test_listing_with_nothing_wired(
    scenario: ListingStep,
    adapter_with_nothing_wired: EntityAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter_with_nothing_wired, engine)
