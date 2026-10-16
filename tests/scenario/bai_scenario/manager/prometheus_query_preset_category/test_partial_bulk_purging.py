"""카테고리 여럿 purge."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override
from uuid import UUID

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.common import PartialBulkPayload
from ai.backend.common.dto.manager.v2.prometheus_query_preset_category.request import (
    PartialBulkPurgeQueryPresetCategoriesInput,
)
from ai.backend.common.dto.manager.v2.prometheus_query_preset_category.response import (
    CategoryNode,
)
from ai.backend.manager.api.adapters.prometheus_query_preset_category.adapter import (
    PrometheusQueryPresetCategoryAdapter,
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
from bai_scenario.components.prometheus_query_preset_category import (
    ManyCategoriesAndACaller,
    ManyCategoriesAndSomeone,
    NothingIsProcessed,
    node_of,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Adapter = PrometheusQueryPresetCategoryAdapter
type Purged = PartialBulkPayload[CategoryNode]
type PurgingStep = Scenario[TestSeedingSession, ManyCategoriesAndACaller, Adapter, Purged]


@dataclass(frozen=True)
class PurgingEveryCategory(When[ManyCategoriesAndACaller, Adapter, Purged]):
    """미리 만들어 둔 카테고리들을 한 번에 purge 한다. `missing`이 있으면 그 id 도 함께 넣는다."""

    missing: UUID | None = None

    @override
    def operation(self) -> str:
        return "partial_bulk_purge"

    @override
    def describe(self, laid: ManyCategoriesAndACaller) -> str:
        besides = " 와 없는 id 하나" if self.missing is not None else ""
        return f"{laid.caller.username}이 카테고리 {len(laid.laid)}개{besides}를 한 번에 purge 함"

    @override
    async def call(self, adapter: Adapter, laid: ManyCategoriesAndACaller) -> Purged:
        ids: list[UUID] = [category.id for category in laid.laid]
        if self.missing is not None:
            ids.append(self.missing)
        with ActingAs(laid.caller):
            return await adapter.partial_bulk_purge(
                PartialBulkPurgeQueryPresetCategoriesInput(ids=ids)
            )


@dataclass(frozen=True)
class EveryCategoryIsPurged(Then[ManyCategoriesAndACaller, Purged]):
    """대상이 모두 지워지기 전 모습으로 처리된 목록에 오고, 없는 id 만 실패 목록에 온다."""

    missing: UUID

    @override
    def says(self) -> str:
        return (
            "대상 카테고리가 모두 지워지기 전 모습으로 오고, 없는 id 는 대상이 없다는 이유로 "
            "실패 목록에 온다"
        )

    @override
    def look(self, laid: ManyCategoriesAndACaller, answered: Answered[Purged]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        verdicts: list[Verdict] = [
            Same("successes count", len(payload.successes), len(laid.laid)),
            Same("failed count", len(payload.failed), 1),
        ]
        for i, (node, category) in enumerate(zip(payload.successes, laid.laid, strict=False)):
            verdicts.append(
                Held[CategoryNode](
                    f"successes[{i}]", node, SameAs(node_of(category), "대상 카테고리 전체")
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
    Scenario[TestSeedingSession, ManyCategoriesAndACaller, Adapter, Purged]
):
    missing: UUID = UUID(int=1)

    @override
    def summary(self) -> str:
        return "purging-several-categories-answers-for-the-missing-one"

    @override
    def describe(self) -> str:
        return (
            "슈퍼관리자가 카테고리 둘과 없는 id 하나를 한 번에 purge 하면, 둘은 지워지기 전 모습으로 "
            "오고 없는 id 는 대상이 없다는 이유로 실패 목록에 온다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyCategoriesAndACaller]:
        return ManyCategoriesAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyCategoriesAndACaller, Adapter, Purged]:
        return PurgingEveryCategory(missing=self.missing)

    @override
    def then(self) -> Then[ManyCategoriesAndACaller, Purged]:
        return EveryCategoryIsPurged(missing=self.missing)


@dataclass(frozen=True)
class AUserGrantedNothingPurgesNone(
    Scenario[TestSeedingSession, ManyCategoriesAndACaller, Adapter, Purged]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-purges-none-of-several-categories"

    @override
    def describe(self) -> str:
        return (
            "아무 권한도 받지 않은 사용자가 카테고리 여럿을 한 번에 purge 하려 하면, 지워진 것 없이 "
            "모두 권한이 없다는 이유로 실패 목록에 온다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyCategoriesAndACaller]:
        return ManyCategoriesAndSomeone()

    @override
    def when(self) -> When[ManyCategoriesAndACaller, Adapter, Purged]:
        return PurgingEveryCategory()

    @override
    def then(self) -> Then[ManyCategoriesAndACaller, Purged]:
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
