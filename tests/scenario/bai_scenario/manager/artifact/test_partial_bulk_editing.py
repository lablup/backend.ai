"""아티팩트 여럿 수정하기."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.artifact.request import (
    PartialBulkUpdateArtifactItemInput,
    PartialBulkUpdateArtifactsInput,
    UpdateArtifactInput,
)
from ai.backend.common.dto.manager.v2.artifact.response import ArtifactNode
from ai.backend.common.dto.manager.v2.common import PartialBulkPayload
from ai.backend.manager.api.adapters.artifact.adapter import ArtifactAdapter
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Scenario, Then, When
from bai_scenario.components.artifact import (
    ArtifactLook,
    EveryTargetComesBack,
    ManyArtifactsAndACaller,
    ManyArtifactsAndSomeone,
    NothingIsProcessed,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

EDITED = "한 번에 고친 설명"

type Edited = PartialBulkPayload[ArtifactNode]
type ArtifactStep = Scenario[TestSeedingSession, ManyArtifactsAndACaller, ArtifactAdapter, Edited]


@dataclass(frozen=True)
class EditingEveryTarget(When[ManyArtifactsAndACaller, ArtifactAdapter, Edited]):
    """대상 아티팩트들의 설명을 한 번에 고친다."""

    @override
    def operation(self) -> str:
        return "partial_bulk_update"

    @override
    def describe(self, laid: ManyArtifactsAndACaller) -> str:
        return f"{laid.caller.username}이 아티팩트 {len(laid.laid)}개의 설명을 한 번에 고침"

    @override
    async def call(self, adapter: ArtifactAdapter, laid: ManyArtifactsAndACaller) -> Edited:
        with ActingAs(laid.caller):
            return await adapter.partial_bulk_update(
                PartialBulkUpdateArtifactsInput(
                    items=[
                        PartialBulkUpdateArtifactItemInput(
                            id=artifact.id, input=UpdateArtifactInput(description=EDITED)
                        )
                        for artifact in laid.laid
                    ]
                )
            )


@dataclass(frozen=True)
class TheSuperadminEditsSeveralArtifacts(
    Scenario[TestSeedingSession, ManyArtifactsAndACaller, ArtifactAdapter, Edited]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-edits-several-artifacts-at-once"

    @override
    def describe(self) -> str:
        return (
            "슈퍼관리자가 아티팩트 여럿의 설명을 한 번에 바꾸면, 모두 새 설명으로 오고 "
            "실패한 것은 없다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyArtifactsAndACaller]:
        return ManyArtifactsAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyArtifactsAndACaller, ArtifactAdapter, Edited]:
        return EditingEveryTarget()

    @override
    def then(self) -> Then[ManyArtifactsAndACaller, Edited]:
        return EveryTargetComesBack(started=self.started, expected=ArtifactLook(described=EDITED))


@dataclass(frozen=True)
class AUserGrantedNothingEditsNone(
    Scenario[TestSeedingSession, ManyArtifactsAndACaller, ArtifactAdapter, Edited]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-edits-none-of-several-artifacts"

    @override
    def describe(self) -> str:
        return (
            "아무 권한도 받지 않은 사용자가 아티팩트 여럿을 한 번에 고치려 하면, 고쳐진 것 없이 "
            "모두 권한이 없다는 이유로 실패 목록에 온다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyArtifactsAndACaller]:
        return ManyArtifactsAndSomeone()

    @override
    def when(self) -> When[ManyArtifactsAndACaller, ArtifactAdapter, Edited]:
        return EditingEveryTarget()

    @override
    def then(self) -> Then[ManyArtifactsAndACaller, Edited]:
        return NothingIsProcessed(reason="Insufficient permission")


SCENARIOS: list[ArtifactStep] = [
    TheSuperadminEditsSeveralArtifacts(started=datetime.now(UTC)),
    AUserGrantedNothingEditsNone(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_partial_bulk_editing(
    scenario: ArtifactStep, adapter: ArtifactAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
