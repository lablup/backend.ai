"""프리셋 여럿 purge."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override
from uuid import UUID, uuid4

import pytest

from ai.backend.common.data.permission.types import Permission
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.common import PartialBulkPayload
from ai.backend.common.dto.manager.v2.prometheus_query_preset.request import (
    PartialBulkPurgeQueryDefinitionsInput,
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
from bai_scenario.components.domain import Mentions
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
        besides_en = " and one absent id" if self.missing is not None else ""
        return Says(
            f"{laid.caller.username}이 프리셋 {len(laid.laid)}개{besides}를 한 번에 purge 합니다",
            english=(f"{laid.caller.username} purges {len(laid.laid)} presets at once{besides_en}"),
        )

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
        return Says(
            "대상 프리셋이 모두 삭제되기 전 모습으로 오고, 없는 id 는 대상이 없다는 이유로 "
            "실패 목록에 옵니다",
            english=(
                "every target preset comes back as it was before deletion, and the absent id "
                "comes back in the failed list because the target is not found"
            ),
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
                    f"successes[{i}]",
                    node,
                    SameAs(
                        node_of(preset),
                        Says("대상 프리셋 전체", english="the whole target preset"),
                    ),
                )
            )
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
        return Says(
            "superadmin 이 프리셋 둘과 없는 id 하나를 한 번에 purge 하면, 둘은 삭제되기 전 "
            "모습으로 오고 없는 id 는 대상이 없다는 이유로 실패 목록에 옵니다",
            english=(
                "when the superadmin purges two presets and one absent id at once, the two "
                "come back as they were before deletion and the absent id comes back in the "
                "failed list because the target is not found"
            ),
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
        return Says(
            "아무 권한도 받지 않은 사용자가 프리셋 여럿을 한 번에 purge 하려 하면, 삭제된 것 "
            "없이 모두 권한이 없다는 이유로 실패 목록에 옵니다",
            english=(
                "when a user granted nothing tries to purge several presets at once, nothing "
                "is deleted and all come back in the failed list for lack of permission"
            ),
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


@dataclass(frozen=True)
class TheGrantedOneIsPurgedAndTheAbsentOneIsDenied(Then[ManyPresetsAndACaller, Purged]):
    """권한을 받은 대상은 지워지기 전 모습으로 오고, 권한이 없는 항목은 실패 목록에 온다."""

    missing: UUID

    @override
    def says(self) -> str:
        return Says(
            "권한을 받은 프리셋은 삭제되기 전 모습으로 오고, 권한이 없는 항목은 "
            "권한 검사의 이유로 실패 목록에 옵니다",
            english=(
                "the preset the caller was granted comes back as it was before deletion, and "
                "the item the caller has no permission on comes back in the failed list for "
                "the permission check"
            ),
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
                    f"successes[{i}]",
                    node,
                    SameAs(
                        node_of(preset),
                        Says("대상 프리셋 전체", english="the whole target preset"),
                    ),
                )
            )
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
class AUserGrantedPurgePurgesOnlyWhatItMay(
    Scenario[TestSeedingSession, ManyPresetsAndACaller, Adapter, Purged]
):
    missing: UUID = uuid4()

    @override
    def summary(self) -> str:
        return "a-user-granted-purge-purges-only-what-it-may"

    @override
    def describe(self) -> str:
        return Says(
            "purge 권한을 받은 사용자가 프리셋 하나와 없는 id 하나를 한 번에 purge 하면, "
            "프리셋은 삭제되기 전 모습으로 오고 없는 id 는 권한 검사의 이유로 실패 목록에 옵니다",
            english=(
                "when a user granted purge purges one preset and one absent id at once, the "
                "preset comes back as it was before deletion and the absent id comes back in "
                "the failed list for the permission check"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyPresetsAndACaller]:
        return ManyPresetsAndSomeoneGranted(permission=Permission.HARD_DELETE, besides=0)

    @override
    def when(self) -> When[ManyPresetsAndACaller, Adapter, Purged]:
        return PurgingEveryPreset(missing=self.missing)

    @override
    def then(self) -> Then[ManyPresetsAndACaller, Purged]:
        return TheGrantedOneIsPurgedAndTheAbsentOneIsDenied(missing=self.missing)


@dataclass(frozen=True)
class PurgingAsNobody(When[ManyPresetsAndACaller, Adapter, Purged]):
    """사용자 컨텍스트 없이 프리셋 여럿을 purge 한다."""

    @override
    def operation(self) -> str:
        return "partial_bulk_purge"

    @override
    def describe(self, laid: ManyPresetsAndACaller) -> str:
        return Says(
            "사용자 컨텍스트 없이 프리셋을 한 번에 purge 합니다",
            english="purges presets at once without a user context",
        )

    @override
    async def call(self, adapter: Adapter, laid: ManyPresetsAndACaller) -> Purged:
        ids: list[UUID] = [preset.id for preset in laid.laid]
        return await adapter.partial_bulk_purge(PartialBulkPurgeQueryDefinitionsInput(ids=ids))


@dataclass(frozen=True)
class ACallCarryingNoUserMayNotPurge(
    Scenario[TestSeedingSession, ManyPresetsAndACaller, Adapter, Purged]
):
    @override
    def summary(self) -> str:
        return "a-call-carrying-no-user-may-not-purge-several-presets"

    @override
    def describe(self) -> str:
        return Says(
            "프리셋이 있고 사용자 컨텍스트 없이 한 번에 purge 하면, 호출자를 알 수 없어 거부됩니다",
            english=(
                "when presets exist and they are purged at once without a user context, it is "
                "rejected because the caller cannot be known"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyPresetsAndACaller]:
        return ManyPresetsAndSomeone(besides=0)

    @override
    def when(self) -> When[ManyPresetsAndACaller, Adapter, Purged]:
        return PurgingAsNobody()

    @override
    def then(self) -> Then[ManyPresetsAndACaller, Purged]:
        return TheCallIsRefused(UnreachableError)


SCENARIOS: list[PurgingStep] = [
    PurgingAnswersForTheMissingOne(),
    AUserGrantedNothingPurgesNone(),
    AUserGrantedPurgePurgesOnlyWhatItMay(),
    ACallCarryingNoUserMayNotPurge(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_partial_bulk_purging(
    scenario: PurgingStep, adapter: Adapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
