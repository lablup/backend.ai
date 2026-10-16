"""Reservoir 레지스트리 하나 purge 하기."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

import pytest

from ai.backend.common.dto.manager.v2.reservoir_registry.response import (
    PurgeReservoirRegistryPayload,
)
from ai.backend.manager.api.adapters.reservoir_registry.adapter import (
    ReservoirRegistryAdapter,
)
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Scenario, Then, When
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.reservoir_registry import (
    ARegistryAndACaller,
    ARegistryAndSomeone,
    ThePurgedIdComesBack,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Purged = PurgeReservoirRegistryPayload
type PurgingStep = Scenario[
    TestSeedingSession, ARegistryAndACaller, ReservoirRegistryAdapter, Purged
]


@dataclass(frozen=True)
class Purging(When[ARegistryAndACaller, ReservoirRegistryAdapter, Purged]):
    """미리 만들어 둔 레지스트리를 purge 한다."""

    @override
    def operation(self) -> str:
        return "purge"

    @override
    def describe(self, laid: ARegistryAndACaller) -> str:
        return f"{laid.caller.username}이 {laid.registry.name}을 purge 함"

    @override
    async def call(self, adapter: ReservoirRegistryAdapter, laid: ARegistryAndACaller) -> Purged:
        with ActingAs(laid.caller):
            return await adapter.purge(laid.registry.id)


@dataclass(frozen=True)
class AUserGrantedPurgePurges(
    Scenario[TestSeedingSession, ARegistryAndACaller, ReservoirRegistryAdapter, Purged]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-purge-purges-a-registry"

    @override
    def describe(self) -> str:
        return "레지스트리 purge 권한을 받은 사용자가 purge 하면, purge 한 레지스트리의 id 가 온다"

    @override
    def given(self) -> Given[TestSeedingSession, ARegistryAndACaller]:
        return ARegistryAndSomeone(granted=(Permission.HARD_DELETE,))

    @override
    def when(self) -> When[ARegistryAndACaller, ReservoirRegistryAdapter, Purged]:
        return Purging()

    @override
    def then(self) -> Then[ARegistryAndACaller, Purged]:
        return ThePurgedIdComesBack()


@dataclass(frozen=True)
class AUserGrantedNothingMayNotPurge(
    Scenario[TestSeedingSession, ARegistryAndACaller, ReservoirRegistryAdapter, Purged]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-purge-a-registry"

    @override
    def describe(self) -> str:
        return "아무 권한도 받지 않은 사용자가 purge 하려 하면 권한 부족으로 거부된다"

    @override
    def given(self) -> Given[TestSeedingSession, ARegistryAndACaller]:
        return ARegistryAndSomeone()

    @override
    def when(self) -> When[ARegistryAndACaller, ReservoirRegistryAdapter, Purged]:
        return Purging()

    @override
    def then(self) -> Then[ARegistryAndACaller, Purged]:
        return TheCallIsRefused(NotEnoughPermission)


SCENARIOS: list[PurgingStep] = [
    AUserGrantedPurgePurges(),
    AUserGrantedNothingMayNotPurge(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_purging(
    scenario: PurgingStep, adapter: ReservoirRegistryAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
