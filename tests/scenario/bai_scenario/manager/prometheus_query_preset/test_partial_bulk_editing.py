"""프리셋 여럿 수정하기."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override
from uuid import UUID

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.common import PartialBulkPayload
from ai.backend.common.dto.manager.v2.prometheus_query_preset.request import (
    ModifyQueryDefinitionInput,
    PartialBulkUpdateQueryDefinitionItemInput,
    PartialBulkUpdateQueryDefinitionsInput,
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
from bai_scenario.components.domain import Mentions, WrittenByThisRun
from bai_scenario.components.prometheus_query_preset import (
    ManyPresetsAndACaller,
    ManyPresetsAndSomeone,
    NothingIsProcessed,
    node_of,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

EDITED = "한 번에 고친 설명"
UNKNOWN_PLACEHOLDER = "rate(container_cpu_seconds_total[${{unknown}}])"

type Adapter = PrometheusQueryPresetAdapter
type Edited = PartialBulkPayload[QueryDefinitionNode]
type EditingStep = Scenario[TestSeedingSession, ManyPresetsAndACaller, Adapter, Edited]


@dataclass(frozen=True)
class EditingEveryPreset(When[ManyPresetsAndACaller, Adapter, Edited]):
    """미리 만들어 둔 프리셋들의 설명을 한 번에 고친다. `broken`이면 첫째의 템플릿도 잘못된 값으로 고친다."""

    broken: bool = False

    @override
    def operation(self) -> str:
        return "partial_bulk_update"

    @override
    def describe(self, laid: ManyPresetsAndACaller) -> str:
        besides = ", 첫째는 템플릿도 잘못된 값으로" if self.broken else ""
        return f"{laid.caller.username}이 프리셋 {len(laid.laid)}개의 설명을 한 번에 고침{besides}"

    def _asked(self, at: int) -> ModifyQueryDefinitionInput:
        if self.broken and at == 0:
            return ModifyQueryDefinitionInput(
                description=EDITED, query_template=UNKNOWN_PLACEHOLDER
            )
        return ModifyQueryDefinitionInput(description=EDITED)

    @override
    async def call(self, adapter: Adapter, laid: ManyPresetsAndACaller) -> Edited:
        items = [
            PartialBulkUpdateQueryDefinitionItemInput(id=preset.id, input=self._asked(at))
            for at, preset in enumerate(laid.laid)
        ]
        with ActingAs(laid.caller):
            return await adapter.partial_bulk_update(
                PartialBulkUpdateQueryDefinitionsInput(items=items)
            )


@dataclass(frozen=True)
class EveryPresetIsEdited(Then[ManyPresetsAndACaller, Edited]):
    """대상이 모두 새 설명을 싣고 처리된 목록에 온다. `broken`이면 첫째만 실패 목록에 온다."""

    started: datetime
    broken: bool = False

    @override
    def says(self) -> str:
        if self.broken:
            return (
                "템플릿이 잘못된 첫째는 그 이유로 실패 목록에 오고, 나머지는 새 설명으로 처리된 "
                "목록에 온다"
            )
        return "대상 프리셋이 모두 새 설명으로 오고, 실패한 것은 없다"

    @override
    def look(self, laid: ManyPresetsAndACaller, answered: Answered[Edited]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        targets = laid.laid[1:] if self.broken else laid.laid
        written = WrittenByThisRun(self.started)
        verdicts: list[Verdict] = [Same("successes count", len(payload.successes), len(targets))]
        for i, (node, preset) in enumerate(zip(payload.successes, targets, strict=False)):
            wanted = node_of(preset).model_copy(update={"description": EDITED})
            verdicts += [
                Held[QueryDefinitionNode](
                    f"successes[{i}]",
                    node.model_copy(update={"updated_at": wanted.updated_at}),
                    SameAs(wanted, "새 설명을 실은 대상 프리셋 전체"),
                ),
                Held(f"successes[{i}].updated_at", node.updated_at, written),
            ]
        if not self.broken:
            return [*verdicts, Same("failed", payload.failed, [])]
        verdicts.append(Same("failed count", len(payload.failed), 1))
        for failure in payload.failed:
            verdicts += [
                Held[UUID]("failed[0].id", failure.id, SameAs(laid.laid[0].id, "첫째 프리셋의 id")),
                Held(
                    "failed[0].message",
                    failure.message,
                    Mentions("Unsupported template variable"),
                ),
            ]
        return verdicts


@dataclass(frozen=True)
class TheSuperadminEditsSeveralPresets(
    Scenario[TestSeedingSession, ManyPresetsAndACaller, Adapter, Edited]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-edits-several-presets-at-once"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 프리셋 여럿의 설명을 한 번에 바꾸면, 모두 새 설명으로 오고 실패한 것은 없다"

    @override
    def given(self) -> Given[TestSeedingSession, ManyPresetsAndACaller]:
        return ManyPresetsAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyPresetsAndACaller, Adapter, Edited]:
        return EditingEveryPreset()

    @override
    def then(self) -> Then[ManyPresetsAndACaller, Edited]:
        return EveryPresetIsEdited(started=self.started)


@dataclass(frozen=True)
class ABrokenTemplateFailsOnlyItsOwnItem(
    Scenario[TestSeedingSession, ManyPresetsAndACaller, Adapter, Edited]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-broken-template-fails-only-the-preset-it-was-meant-for"

    @override
    def describe(self) -> str:
        return (
            "슈퍼관리자가 프리셋 여럿을 한 번에 고치며 하나에 잘못된 템플릿을 주면, 그 하나만 "
            "템플릿 검사의 이유로 실패 목록에 오고 나머지는 고쳐진다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyPresetsAndACaller]:
        return ManyPresetsAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyPresetsAndACaller, Adapter, Edited]:
        return EditingEveryPreset(broken=True)

    @override
    def then(self) -> Then[ManyPresetsAndACaller, Edited]:
        return EveryPresetIsEdited(started=self.started, broken=True)


@dataclass(frozen=True)
class AUserGrantedNothingEditsNone(
    Scenario[TestSeedingSession, ManyPresetsAndACaller, Adapter, Edited]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-edits-none-of-several-presets"

    @override
    def describe(self) -> str:
        return (
            "아무 권한도 받지 않은 사용자가 프리셋 여럿을 한 번에 고치려 하면, 고쳐진 것 없이 "
            "모두 권한이 없다는 이유로 실패 목록에 온다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyPresetsAndACaller]:
        return ManyPresetsAndSomeone()

    @override
    def when(self) -> When[ManyPresetsAndACaller, Adapter, Edited]:
        return EditingEveryPreset()

    @override
    def then(self) -> Then[ManyPresetsAndACaller, Edited]:
        return NothingIsProcessed(reason="Insufficient permission")


SCENARIOS: list[EditingStep] = [
    TheSuperadminEditsSeveralPresets(started=datetime.now(UTC)),
    ABrokenTemplateFailsOnlyItsOwnItem(started=datetime.now(UTC)),
    AUserGrantedNothingEditsNone(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_partial_bulk_editing(
    scenario: EditingStep, adapter: Adapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
