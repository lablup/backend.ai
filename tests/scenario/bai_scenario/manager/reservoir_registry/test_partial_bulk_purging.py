"""Reservoir 레지스트리 여럿 purge 하기."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override
from uuid import UUID

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.reservoir_registry.request import (
    PartialBulkPurgeReservoirRegistriesInput,
)
from ai.backend.manager.api.adapters.reservoir_registry.adapter import (
    ReservoirRegistryAdapter,
)
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Scenario, Then, When
from bai_scenario.components.reservoir_registry import (
    EveryTargetIsPurged,
    ManyRegistriesAndACaller,
    ManyRegistriesAndSomeone,
    NothingIsProcessed,
    Purged,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type PurgingStep = Scenario[
    TestSeedingSession, ManyRegistriesAndACaller, ReservoirRegistryAdapter, Purged
]


@dataclass(frozen=True)
class PurgingEveryTarget(When[ManyRegistriesAndACaller, ReservoirRegistryAdapter, Purged]):
    """대상 레지스트리들을 한 번에 purge 한다. `missing`이 있으면 그 id 도 함께 넣는다."""

    missing: UUID | None = None

    @override
    def operation(self) -> str:
        return "partial_bulk_purge"

    @override
    def describe(self, laid: ManyRegistriesAndACaller) -> str:
        besides = " 와 없는 id 하나" if self.missing is not None else ""
        return f"{laid.caller.username}이 레지스트리 {len(laid.laid)}개{besides}를 한 번에 purge 함"

    @override
    async def call(
        self, adapter: ReservoirRegistryAdapter, laid: ManyRegistriesAndACaller
    ) -> Purged:
        ids: list[UUID] = [registry.id for registry in laid.laid]
        if self.missing is not None:
            ids.append(self.missing)
        with ActingAs(laid.caller):
            return await adapter.partial_bulk_purge(
                PartialBulkPurgeReservoirRegistriesInput(ids=ids)
            )


@dataclass(frozen=True)
class AUserGrantedPurgePurgesSeveral(
    Scenario[TestSeedingSession, ManyRegistriesAndACaller, ReservoirRegistryAdapter, Purged]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-purge-purges-several-registries"

    @override
    def describe(self) -> str:
        return (
            "레지스트리 purge 권한을 받은 사용자가 여럿을 한 번에 purge 하면, 모두의 id 가 처리된 "
            "목록에 오고 실패한 것은 없다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyRegistriesAndACaller]:
        return ManyRegistriesAndSomeone(granted=(Permission.HARD_DELETE,))

    @override
    def when(self) -> When[ManyRegistriesAndACaller, ReservoirRegistryAdapter, Purged]:
        return PurgingEveryTarget()

    @override
    def then(self) -> Then[ManyRegistriesAndACaller, Purged]:
        return EveryTargetIsPurged()


@dataclass(frozen=True)
class PurgingAnswersForTheMissingOne(
    Scenario[TestSeedingSession, ManyRegistriesAndACaller, ReservoirRegistryAdapter, Purged]
):
    missing: UUID = UUID(int=1)

    @override
    def summary(self) -> str:
        return "purging-several-answers-for-the-missing-one"

    @override
    def describe(self) -> str:
        return (
            "슈퍼관리자가 레지스트리 둘과 없는 id 하나를 한 번에 purge 하면, 둘의 id 는 처리된 "
            "목록에, 없는 id 는 대상이 없다는 이유로 실패 목록에 온다. 슈퍼관리자는 검사를 모두 "
            "통과하므로 대상 없음이 그대로 드러난다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyRegistriesAndACaller]:
        return ManyRegistriesAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyRegistriesAndACaller, ReservoirRegistryAdapter, Purged]:
        return PurgingEveryTarget(missing=self.missing)

    @override
    def then(self) -> Then[ManyRegistriesAndACaller, Purged]:
        return EveryTargetIsPurged(missing=self.missing)


@dataclass(frozen=True)
class AUserGrantedNothingPurgesNone(
    Scenario[TestSeedingSession, ManyRegistriesAndACaller, ReservoirRegistryAdapter, Purged]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-purges-none-of-several-registries"

    @override
    def describe(self) -> str:
        return (
            "아무 권한도 받지 않은 사용자가 레지스트리 여럿을 한 번에 purge 하려 하면, purge 된 것 "
            "없이 모두 권한이 없다는 이유로 실패 목록에 온다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyRegistriesAndACaller]:
        return ManyRegistriesAndSomeone()

    @override
    def when(self) -> When[ManyRegistriesAndACaller, ReservoirRegistryAdapter, Purged]:
        return PurgingEveryTarget()

    @override
    def then(self) -> Then[ManyRegistriesAndACaller, Purged]:
        return NothingIsProcessed(reason="Insufficient permission")


SCENARIOS: list[PurgingStep] = [
    AUserGrantedPurgePurgesSeveral(),
    PurgingAnswersForTheMissingOne(),
    AUserGrantedNothingPurgesNone(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_partial_bulk_purging(
    scenario: PurgingStep, adapter: ReservoirRegistryAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
