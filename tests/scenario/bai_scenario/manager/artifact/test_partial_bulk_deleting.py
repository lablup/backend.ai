"""아티팩트 여럿 soft delete, restore."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override
from uuid import UUID

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.artifact.request import (
    PartialBulkDeleteArtifactsInput,
    PartialBulkRestoreArtifactsInput,
)
from ai.backend.common.dto.manager.v2.artifact.response import ArtifactNode
from ai.backend.common.dto.manager.v2.artifact.types import ArtifactAvailability
from ai.backend.common.dto.manager.v2.common import PartialBulkPayload
from ai.backend.manager.api.adapters.artifact.adapter import ArtifactAdapter
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Says, Scenario, Then, When
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

type Deleted = PartialBulkPayload[ArtifactNode]
type ArtifactStep = Scenario[TestSeedingSession, ManyArtifactsAndACaller, ArtifactAdapter, Deleted]


@dataclass(frozen=True)
class SoftDeletingEveryTarget(When[ManyArtifactsAndACaller, ArtifactAdapter, Deleted]):
    """대상 아티팩트들을 한 번에 soft delete 한다. `missing`이 있으면 그 id 도 함께 넣는다."""

    missing: UUID | None = None

    @override
    def operation(self) -> str:
        return "partial_bulk_delete"

    @override
    def describe(self, laid: ManyArtifactsAndACaller) -> str:
        besides_ko = "와 존재하지 않는 id 하나" if self.missing is not None else ""
        besides_en = " and one id that does not exist" if self.missing is not None else ""
        return Says(
            f"{laid.caller.username}이 아티팩트 {len(laid.laid)}개{besides_ko}를 한 번에 "
            "soft delete 합니다",
            english=(
                f"{laid.caller.username} soft deletes {len(laid.laid)} artifacts{besides_en} "
                "at once"
            ),
        )

    @override
    async def call(self, adapter: ArtifactAdapter, laid: ManyArtifactsAndACaller) -> Deleted:
        ids: list[UUID] = [artifact.id for artifact in laid.laid]
        if self.missing is not None:
            ids.append(self.missing)
        with ActingAs(laid.caller):
            return await adapter.partial_bulk_delete(PartialBulkDeleteArtifactsInput(ids=ids))


@dataclass(frozen=True)
class SoftDeletingThenRestoringEveryTarget(When[ManyArtifactsAndACaller, ArtifactAdapter, Deleted]):
    """대상 아티팩트들을 한 번에 soft delete 했다가 한 번에 restore 한다. restore 의 답을 준다."""

    @override
    def operation(self) -> str:
        return "partial_bulk_restore"

    @override
    def describe(self, laid: ManyArtifactsAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 아티팩트 {len(laid.laid)}개를 한 번에 soft delete "
            "했다가 한 번에 restore 합니다",
            english=(
                f"{laid.caller.username} soft deletes {len(laid.laid)} artifacts at once and "
                "then restores them at once"
            ),
        )

    @override
    async def call(self, adapter: ArtifactAdapter, laid: ManyArtifactsAndACaller) -> Deleted:
        ids: list[UUID] = [artifact.id for artifact in laid.laid]
        with ActingAs(laid.caller):
            await adapter.partial_bulk_delete(PartialBulkDeleteArtifactsInput(ids=ids))
            return await adapter.partial_bulk_restore(PartialBulkRestoreArtifactsInput(ids=ids))


@dataclass(frozen=True)
class SoftDeletingAnswersForTheMissingOne(
    Scenario[TestSeedingSession, ManyArtifactsAndACaller, ArtifactAdapter, Deleted]
):
    started: datetime
    missing: UUID = UUID(int=1)

    @override
    def summary(self) -> str:
        return "soft-deleting-several-answers-for-the-missing-one"

    @override
    def describe(self) -> str:
        return Says(
            "아티팩트 둘과 존재하지 않는 id 하나를 한 번에 soft delete 하면, 둘은 삭제됨 상태로 "
            "오고 존재하지 않는 id 는 대상이 없다는 이유로 실패 목록에 옵니다",
            english=(
                "when two artifacts and one id that does not exist are soft deleted at once, "
                "the two come back in the deleted state and the id that does not exist comes "
                "back in the failed list because there is no such target"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyArtifactsAndACaller]:
        return ManyArtifactsAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyArtifactsAndACaller, ArtifactAdapter, Deleted]:
        return SoftDeletingEveryTarget(missing=self.missing)

    @override
    def then(self) -> Then[ManyArtifactsAndACaller, Deleted]:
        return EveryTargetComesBack(
            started=self.started,
            expected=ArtifactLook(availability=ArtifactAvailability.DELETED),
            missing=self.missing,
        )


@dataclass(frozen=True)
class AUserGrantedNothingSoftDeletesNone(
    Scenario[TestSeedingSession, ManyArtifactsAndACaller, ArtifactAdapter, Deleted]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-soft-deletes-none-of-several-artifacts"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 아티팩트 여럿을 한 번에 soft delete 하려 하면, "
            "soft delete 된 것 없이 모두 권한이 없다는 이유로 실패 목록에 옵니다",
            english=(
                "when a user granted nothing tries to soft delete several artifacts at once, "
                "nothing is soft deleted and all come back in the failed list because there is "
                "no permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyArtifactsAndACaller]:
        return ManyArtifactsAndSomeone()

    @override
    def when(self) -> When[ManyArtifactsAndACaller, ArtifactAdapter, Deleted]:
        return SoftDeletingEveryTarget()

    @override
    def then(self) -> Then[ManyArtifactsAndACaller, Deleted]:
        return NothingIsProcessed(reason="Insufficient permission")


@dataclass(frozen=True)
class RestoringBringsSeveralBack(
    Scenario[TestSeedingSession, ManyArtifactsAndACaller, ArtifactAdapter, Deleted]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "restoring-several-brings-them-back"

    @override
    def describe(self) -> str:
        return Says(
            "soft delete 된 아티팩트 여럿을 한 번에 restore 하면, 모두 살아 있는 상태로 옵니다",
            english=(
                "when several soft-deleted artifacts are restored at once, all come back in "
                "the live state"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyArtifactsAndACaller]:
        return ManyArtifactsAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyArtifactsAndACaller, ArtifactAdapter, Deleted]:
        return SoftDeletingThenRestoringEveryTarget()

    @override
    def then(self) -> Then[ManyArtifactsAndACaller, Deleted]:
        return EveryTargetComesBack(started=self.started, expected=ArtifactLook())


SCENARIOS: list[ArtifactStep] = [
    SoftDeletingAnswersForTheMissingOne(started=datetime.now(UTC)),
    AUserGrantedNothingSoftDeletesNone(),
    RestoringBringsSeveralBack(started=datetime.now(UTC)),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_partial_bulk_deleting(
    scenario: ArtifactStep, adapter: ArtifactAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
