"""프리셋 여럿 수정하기."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override
from uuid import UUID, uuid4

import pytest

from ai.backend.common.data.permission.types import Permission
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
from ai.backend.common.exception import UnreachableError
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
    Says,
    Scenario,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.domain import Mentions, WrittenByThisRun
from bai_scenario.components.prometheus_query_preset import (
    ManyPresetsAndACaller,
    ManyPresetsAndSomeone,
    ManyPresetsAndSomeoneGranted,
    NothingIsProcessed,
    node_of,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

EDITED = Says("한 번에 수정한 설명", english="a description edited at once")
UNKNOWN_PLACEHOLDER = "rate(container_cpu_seconds_total[${{unknown}}])"

type Adapter = PrometheusQueryPresetAdapter
type Edited = PartialBulkPayload[QueryDefinitionNode]
type EditingStep = Scenario[TestSeedingSession, ManyPresetsAndACaller, Adapter, Edited]


@dataclass(frozen=True)
class EditingEveryPreset(When[ManyPresetsAndACaller, Adapter, Edited]):
    """미리 만들어 둔 프리셋들의 설명을 한 번에 고친다. `broken`이면 첫째의 템플릿도 잘못된 값으로 고친다. `missing`이 있으면 그 id 도 함께 넣는다."""

    broken: bool = False
    missing: UUID | None = None

    @override
    def operation(self) -> str:
        return "partial_bulk_update"

    @override
    def describe(self, laid: ManyPresetsAndACaller) -> str:
        besides = ", 첫째는 템플릿도 잘못된 값으로" if self.broken else ""
        besides_en = ", the first with a broken template too" if self.broken else ""
        if self.missing is not None:
            besides += " 와 없는 id 하나"
            besides_en += " and one absent id"
        return Says(
            f"{laid.caller.username}이 프리셋 {len(laid.laid)}개의 설명을 한 번에 수정합니다{besides}",
            english=(
                f"{laid.caller.username} edits the descriptions of {len(laid.laid)} presets "
                f"at once{besides_en}"
            ),
        )

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
        if self.missing is not None:
            items.append(
                PartialBulkUpdateQueryDefinitionItemInput(
                    id=self.missing, input=ModifyQueryDefinitionInput(description=EDITED)
                )
            )
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
            return Says(
                "템플릿이 잘못된 첫째는 그 이유로 실패 목록에 오고, 나머지는 새 설명으로 처리된 "
                "목록에 옵니다",
                english=(
                    "the first, whose template is broken, comes back in the failed list for "
                    "that reason, and the rest come back in the processed list with the new "
                    "description"
                ),
            )
        return Says(
            "대상 프리셋이 모두 새 설명으로 오고, 실패한 것은 없습니다",
            english=("every target preset comes back with the new description and none failed"),
        )

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
                    SameAs(
                        wanted,
                        Says(
                            "새 설명을 실은 대상 프리셋 전체",
                            english="the whole target preset carrying the new description",
                        ),
                    ),
                ),
                Held(f"successes[{i}].updated_at", node.updated_at, written),
            ]
        if not self.broken:
            return [*verdicts, Same("failed", payload.failed, [])]
        verdicts.append(Same("failed count", len(payload.failed), 1))
        for failure in payload.failed:
            verdicts += [
                Held[UUID](
                    "failed[0].id",
                    failure.id,
                    SameAs(
                        laid.laid[0].id,
                        Says("첫째 프리셋의 id", english="the id of the first preset"),
                    ),
                ),
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
        return Says(
            "superadmin 이 프리셋 여럿의 설명을 한 번에 변경하면, 모두 새 설명으로 오고 실패한 "
            "것은 없습니다",
            english=(
                "when the superadmin changes the descriptions of several presets at once, all "
                "come back with the new description and none failed"
            ),
        )

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
        return Says(
            "superadmin 이 프리셋 여럿을 한 번에 수정하며 하나에 잘못된 템플릿을 주면, 그 하나만 "
            "템플릿 검사의 이유로 실패 목록에 오고 나머지는 수정됩니다",
            english=(
                "when the superadmin edits several presets at once and gives one a broken "
                "template, only that one comes back in the failed list for the template check "
                "and the rest are edited"
            ),
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
        return Says(
            "아무 권한도 받지 않은 사용자가 프리셋 여럿을 한 번에 수정하려 하면, 수정된 것 없이 "
            "모두 권한이 없다는 이유로 실패 목록에 옵니다",
            english=(
                "when a user granted nothing tries to edit several presets at once, nothing "
                "is edited and all come back in the failed list for lack of permission"
            ),
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


@dataclass(frozen=True)
class TheEditedOneComesBackAndTheAbsentOneIsDenied(Then[ManyPresetsAndACaller, Edited]):
    """수정된 대상은 새 설명을 실어 오고, 권한이 없는 항목은 실패 목록에 온다."""

    started: datetime
    missing: UUID

    @override
    def says(self) -> str:
        return Says(
            "수정된 프리셋은 새 설명을 실어 오고, 권한이 없는 항목은 "
            "권한 검사의 이유로 실패 목록에 옵니다",
            english=(
                "the edited preset comes back with the new description, and the item the "
                "caller has no permission on comes back in the failed list for the "
                "permission check"
            ),
        )

    @override
    def look(self, laid: ManyPresetsAndACaller, answered: Answered[Edited]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        written = WrittenByThisRun(self.started)
        verdicts: list[Verdict] = [Same("successes count", len(payload.successes), len(laid.laid))]
        for i, (node, preset) in enumerate(zip(payload.successes, laid.laid, strict=False)):
            wanted = node_of(preset).model_copy(update={"description": EDITED})
            verdicts += [
                Held[QueryDefinitionNode](
                    f"successes[{i}]",
                    node.model_copy(update={"updated_at": wanted.updated_at}),
                    SameAs(
                        wanted,
                        Says(
                            "새 설명을 실은 대상 프리셋 전체",
                            english="the whole target preset carrying the new description",
                        ),
                    ),
                ),
                Held(f"successes[{i}].updated_at", node.updated_at, written),
            ]
        verdicts.append(Same("failed count", len(payload.failed), 1))
        for failure in payload.failed:
            verdicts += [
                Held[UUID](
                    "failed[0].id",
                    failure.id,
                    SameAs(
                        self.missing,
                        Says(
                            "요청에 넣은 없는 id",
                            english="the absent id put in the request",
                        ),
                    ),
                ),
                Held("failed[0].message", failure.message, Mentions("Insufficient permission")),
            ]
        return verdicts


@dataclass(frozen=True)
class AUserGrantedUpdateEditsOnlyWhatItMay(
    Scenario[TestSeedingSession, ManyPresetsAndACaller, Adapter, Edited]
):
    started: datetime
    missing: UUID = uuid4()

    @override
    def summary(self) -> str:
        return "a-user-granted-update-edits-only-what-it-may"

    @override
    def describe(self) -> str:
        return Says(
            "update 권한을 받은 사용자가 프리셋 하나와 없는 id 하나를 한 번에 수정하면, "
            "프리셋은 새 설명으로 오고 없는 id 는 권한 검사의 이유로 실패 목록에 옵니다",
            english=(
                "when a user granted update edits one preset and one absent id at once, the "
                "preset comes back with the new description and the absent id comes back in "
                "the failed list for the permission check"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyPresetsAndACaller]:
        return ManyPresetsAndSomeoneGranted(permission=Permission.UPDATE, besides=0)

    @override
    def when(self) -> When[ManyPresetsAndACaller, Adapter, Edited]:
        return EditingEveryPreset(missing=self.missing)

    @override
    def then(self) -> Then[ManyPresetsAndACaller, Edited]:
        return TheEditedOneComesBackAndTheAbsentOneIsDenied(
            started=self.started, missing=self.missing
        )


@dataclass(frozen=True)
class EditingAsNobody(When[ManyPresetsAndACaller, Adapter, Edited]):
    """사용자 컨텍스트 없이 프리셋 여럿의 설명을 고친다."""

    @override
    def operation(self) -> str:
        return "partial_bulk_update"

    @override
    def describe(self, laid: ManyPresetsAndACaller) -> str:
        return Says(
            "사용자 컨텍스트 없이 프리셋 설명을 한 번에 수정합니다",
            english="edits the descriptions of presets at once without a user context",
        )

    @override
    async def call(self, adapter: Adapter, laid: ManyPresetsAndACaller) -> Edited:
        items = [
            PartialBulkUpdateQueryDefinitionItemInput(
                id=preset.id, input=ModifyQueryDefinitionInput(description=EDITED)
            )
            for preset in laid.laid
        ]
        return await adapter.partial_bulk_update(
            PartialBulkUpdateQueryDefinitionsInput(items=items)
        )


@dataclass(frozen=True)
class ACallCarryingNoUserMayNotEdit(
    Scenario[TestSeedingSession, ManyPresetsAndACaller, Adapter, Edited]
):
    @override
    def summary(self) -> str:
        return "a-call-carrying-no-user-may-not-edit-several-presets"

    @override
    def describe(self) -> str:
        return Says(
            "프리셋이 있고 사용자 컨텍스트 없이 설명을 한 번에 수정하면, 호출자를 알 수 없어 "
            "거부됩니다",
            english=(
                "when presets exist and their descriptions are edited at once without a user "
                "context, it is rejected because the caller cannot be known"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyPresetsAndACaller]:
        return ManyPresetsAndSomeone(besides=0)

    @override
    def when(self) -> When[ManyPresetsAndACaller, Adapter, Edited]:
        return EditingAsNobody()

    @override
    def then(self) -> Then[ManyPresetsAndACaller, Edited]:
        return TheCallIsRefused(UnreachableError)


SCENARIOS: list[EditingStep] = [
    TheSuperadminEditsSeveralPresets(started=datetime.now(UTC)),
    ABrokenTemplateFailsOnlyItsOwnItem(started=datetime.now(UTC)),
    AUserGrantedNothingEditsNone(),
    AUserGrantedUpdateEditsOnlyWhatItMay(started=datetime.now(UTC)),
    ACallCarryingNoUserMayNotEdit(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_partial_bulk_editing(
    scenario: EditingStep, adapter: Adapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
