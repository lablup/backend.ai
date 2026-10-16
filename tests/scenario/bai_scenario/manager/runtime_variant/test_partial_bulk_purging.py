"""런타임 변형 여럿 purge."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override
from uuid import UUID

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.common import PartialBulkPayload
from ai.backend.common.dto.manager.v2.runtime_variant.request import (
    PartialBulkPurgeRuntimeVariantsInput,
)
from ai.backend.common.dto.manager.v2.runtime_variant.response import RuntimeVariantNode
from ai.backend.manager.api.adapters.runtime_variant.adapter import RuntimeVariantAdapter
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Scenario, Then, When
from bai_scenario.components.runtime_variant import (
    EveryLaidVariantComesBack,
    ManyVariantsAndACaller,
    ManyVariantsAndSomeone,
    NoLaidVariantIsProcessed,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Purged = PartialBulkPayload[RuntimeVariantNode]
type PurgingStep = Scenario[
    TestSeedingSession, ManyVariantsAndACaller, RuntimeVariantAdapter, Purged
]


@dataclass(frozen=True)
class PurgingEveryLaid(When[ManyVariantsAndACaller, RuntimeVariantAdapter, Purged]):
    """미리 만들어 둔 변형들을 한 번에 purge 한다. `missing`이 있으면 그 id 도 함께 넣는다."""

    missing: UUID | None = None

    @override
    def operation(self) -> str:
        return "partial_bulk_purge"

    @override
    def describe(self, laid: ManyVariantsAndACaller) -> str:
        besides = " 와 없는 id 하나" if self.missing is not None else ""
        return f"{laid.caller.username}이 변형 {len(laid.laid)}개{besides}를 한 번에 purge 함"

    @override
    async def call(self, adapter: RuntimeVariantAdapter, laid: ManyVariantsAndACaller) -> Purged:
        ids: list[UUID] = [one.id for one in laid.laid]
        if self.missing is not None:
            ids.append(self.missing)
        with ActingAs(laid.caller):
            return await adapter.partial_bulk_purge(PartialBulkPurgeRuntimeVariantsInput(ids=ids))


@dataclass(frozen=True)
class PurgingAnswersForTheMissingOne(
    Scenario[TestSeedingSession, ManyVariantsAndACaller, RuntimeVariantAdapter, Purged]
):
    started: datetime
    missing: UUID = UUID(int=1)

    @override
    def summary(self) -> str:
        return "purging-several-variants-answers-for-the-missing-one"

    @override
    def describe(self) -> str:
        return (
            "슈퍼관리자가 변형 둘과 없는 id 하나를 한 번에 purge 하면, 둘은 purge 되기 전 모습으로 "
            "처리된 목록에 오고 없는 id 는 실패 목록에 온다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyVariantsAndACaller]:
        return ManyVariantsAndSomeone(role=UserRole.SUPERADMIN, besides=1)

    @override
    def when(self) -> When[ManyVariantsAndACaller, RuntimeVariantAdapter, Purged]:
        return PurgingEveryLaid(missing=self.missing)

    @override
    def then(self) -> Then[ManyVariantsAndACaller, Purged]:
        return EveryLaidVariantComesBack(started=self.started, missing=self.missing)


@dataclass(frozen=True)
class AUserGrantedNothingPurgesNone(
    Scenario[TestSeedingSession, ManyVariantsAndACaller, RuntimeVariantAdapter, Purged]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-purges-none-of-several-variants"

    @override
    def describe(self) -> str:
        return (
            "아무 권한도 없는 사용자가 변형 여럿을 한 번에 purge 하려 하면, purge 된 것 없이 "
            "모두 권한이 없다는 이유로 실패 목록에 온다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyVariantsAndACaller]:
        return ManyVariantsAndSomeone(besides=1)

    @override
    def when(self) -> When[ManyVariantsAndACaller, RuntimeVariantAdapter, Purged]:
        return PurgingEveryLaid()

    @override
    def then(self) -> Then[ManyVariantsAndACaller, Purged]:
        return NoLaidVariantIsProcessed(reason="Insufficient permission")


SCENARIOS: list[PurgingStep] = [
    PurgingAnswersForTheMissingOne(started=datetime.now(UTC)),
    AUserGrantedNothingPurgesNone(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_partial_bulk_purging(
    scenario: PurgingStep, adapter: RuntimeVariantAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
