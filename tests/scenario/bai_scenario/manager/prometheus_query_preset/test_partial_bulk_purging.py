"""프리셋 여럿 purge."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override
from uuid import UUID

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.common import PartialBulkPayload
from ai.backend.common.dto.manager.v2.prometheus_query_preset.request import (
    PartialBulkPurgeQueryDefinitionsInput,
)
from ai.backend.common.dto.manager.v2.prometheus_query_preset.response import (
    QueryDefinitionNode,
)
from ai.backend.manager.api.adapters.prometheus_query_preset.adapter import (
    PrometheusQueryPresetAdapter,
)
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    Refused,
    Same,
    SameAs,
    Scenario,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.domain import Mentions
from bai_scenario.components.prometheus_query_preset import (
    ManyPresetsAndACaller,
    ManyPresetsAndSomeone,
    NothingIsProcessed,
    node_of,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Adapter = PrometheusQueryPresetAdapter
type Purged = PartialBulkPayload[QueryDefinitionNode]
type PurgingStep = Scenario[TestSeedingSession, ManyPresetsAndACaller, Adapter, Purged]


@dataclass(frozen=True)
class PurgingEveryPreset(When[ManyPresetsAndACaller, Adapter, Purged]):
    """미리 만들어 둔 프리셋들을 한 번에 purge 한다. `missing`이 있으면 그 id 도 함께 넣는다."""

    missing: UUID | None = None

    @override
    def operation(self) -> str:
        return "partial_bulk_purge"

    @override
    def describe(self, laid: ManyPresetsAndACaller) -> str:
        besides = " 와 없는 id 하나" if self.missing is not None else ""
        return f"{laid.caller.username}이 프리셋 {len(laid.laid)}개{besides}를 한 번에 purge 함"

    @override
    async def call(self, adapter: Adapter, laid: ManyPresetsAndACaller) -> Purged:
        ids: list[UUID] = [preset.id for preset in laid.laid]
        if self.missing is not None:
            ids.append(self.missing)
        with ActingAs(laid.caller):
            return await adapter.partial_bulk_purge(PartialBulkPurgeQueryDefinitionsInput(ids=ids))


@dataclass(frozen=True)
class EveryPresetIsPurged(Then[ManyPresetsAndACaller, Purged]):
    """대상이 모두 지워지기 전 모습으로 처리된 목록에 오고, 없는 id 만 실패 목록에 온다."""

    missing: UUID

    @override
    def says(self) -> str:
        return (
            "대상 프리셋이 모두 지워지기 전 모습으로 오고, 없는 id 는 대상이 없다는 이유로 "
            "실패 목록에 온다"
        )

    @override
    def look(self, laid: ManyPresetsAndACaller, answered: Answered[Purged]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        verdicts: list[Verdict] = [
            Same("successes count", len(payload.successes), len(laid.laid)),
            Same("failed count", len(payload.failed), 1),
        ]
        for i, (node, preset) in enumerate(zip(payload.successes, laid.laid, strict=False)):
            verdicts.append(
                Held[QueryDefinitionNode](
                    f"successes[{i}]", node, SameAs(node_of(preset), "대상 프리셋 전체")
                )
            )
        for failure in payload.failed:
            verdicts += [
                Held[UUID]("failed[0].id", failure.id, SameAs(self.missing, "요청에 넣은 없는 id")),
                Held("failed[0].message", failure.message, Mentions("not found")),
            ]
        return verdicts


@dataclass(frozen=True)
class PurgingAnswersForTheMissingOne(
    Scenario[TestSeedingSession, ManyPresetsAndACaller, Adapter, Purged]
):
    missing: UUID = UUID(int=1)

    @override
    def summary(self) -> str:
        return "purging-several-presets-answers-for-the-missing-one"

    @override
    def describe(self) -> str:
        return (
            "슈퍼관리자가 프리셋 둘과 없는 id 하나를 한 번에 purge 하면, 둘은 지워지기 전 모습으로 "
            "오고 없는 id 는 대상이 없다는 이유로 실패 목록에 온다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyPresetsAndACaller]:
        return ManyPresetsAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyPresetsAndACaller, Adapter, Purged]:
        return PurgingEveryPreset(missing=self.missing)

    @override
    def then(self) -> Then[ManyPresetsAndACaller, Purged]:
        return EveryPresetIsPurged(missing=self.missing)


@dataclass(frozen=True)
class AUserGrantedNothingPurgesNone(
    Scenario[TestSeedingSession, ManyPresetsAndACaller, Adapter, Purged]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-purges-none-of-several-presets"

    @override
    def describe(self) -> str:
        return (
            "아무 권한도 받지 않은 사용자가 프리셋 여럿을 한 번에 purge 하려 하면, 지워진 것 없이 "
            "모두 권한이 없다는 이유로 실패 목록에 온다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyPresetsAndACaller]:
        return ManyPresetsAndSomeone()

    @override
    def when(self) -> When[ManyPresetsAndACaller, Adapter, Purged]:
        return PurgingEveryPreset()

    @override
    def then(self) -> Then[ManyPresetsAndACaller, Purged]:
        return NothingIsProcessed(reason="Insufficient permission")


SCENARIOS: list[PurgingStep] = [
    PurgingAnswersForTheMissingOne(),
    AUserGrantedNothingPurgesNone(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_partial_bulk_purging(
    scenario: PurgingStep, adapter: Adapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
