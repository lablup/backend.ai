"""아티팩트 여럿을 id 목록으로 soft delete, restore. 여럿 연산이 생기기 전의 호출이다."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override
from uuid import UUID

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.artifact.request import DeleteArtifactsInput
from ai.backend.common.dto.manager.v2.artifact.response import ArtifactNode
from ai.backend.common.dto.manager.v2.artifact.types import ArtifactAvailability
from ai.backend.manager.api.adapters.artifact.adapter import ArtifactAdapter
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Refused,
    Same,
    Scenario,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.artifact import (
    ArtifactLook,
    ManyArtifactsAndACaller,
    ManyArtifactsAndSomeone,
)
from bai_scenario.components.domain import TheCallIsRefused
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Deleted = list[ArtifactNode]
type ArtifactStep = Scenario[TestSeedingSession, ManyArtifactsAndACaller, ArtifactAdapter, Deleted]


@dataclass(frozen=True)
class SoftDeletingByIds(When[ManyArtifactsAndACaller, ArtifactAdapter, Deleted]):
    """대상 아티팩트들을 id 목록으로 soft delete 한다."""

    @override
    def operation(self) -> str:
        return "delete_artifacts"

    @override
    def describe(self, laid: ManyArtifactsAndACaller) -> str:
        return f"{laid.caller.username}이 아티팩트 {len(laid.laid)}개를 id 목록으로 soft delete 함"

    @override
    async def call(self, adapter: ArtifactAdapter, laid: ManyArtifactsAndACaller) -> Deleted:
        with ActingAs(laid.caller):
            payload = await adapter.delete_artifacts(
                DeleteArtifactsInput(artifact_ids=[artifact.id for artifact in laid.laid])
            )
            return payload.artifacts


@dataclass(frozen=True)
class SoftDeletingThenRestoringByIds(When[ManyArtifactsAndACaller, ArtifactAdapter, Deleted]):
    """대상 아티팩트들을 id 목록으로 soft delete 했다가 restore 한다. restore 의 답을 준다."""

    @override
    def operation(self) -> str:
        return "restore_artifacts"

    @override
    def describe(self, laid: ManyArtifactsAndACaller) -> str:
        return (
            f"{laid.caller.username}이 아티팩트 {len(laid.laid)}개를 id 목록으로 soft delete "
            "했다가 restore 함"
        )

    @override
    async def call(self, adapter: ArtifactAdapter, laid: ManyArtifactsAndACaller) -> Deleted:
        ids: list[UUID] = [artifact.id for artifact in laid.laid]
        with ActingAs(laid.caller):
            await adapter.delete_artifacts(DeleteArtifactsInput(artifact_ids=ids))
            return await adapter.restore_artifacts(ids)


@dataclass(frozen=True)
class EveryTargetIsAnswered(Then[ManyArtifactsAndACaller, Deleted]):
    """대상이 모두 같은 상태로 온다."""

    started: datetime
    expected: ArtifactLook

    @override
    def says(self) -> str:
        return "대상 아티팩트가 모두 처리된 모습으로 온다"

    @override
    def look(self, laid: ManyArtifactsAndACaller, answered: Answered[Deleted]) -> list[Verdict]:
        nodes = answered.response
        if nodes is None:
            return [Refused(InsufficientPrivilege, answered.raised)]
        # The answer comes in no set order; both sides are put in id order to pair them.
        answered_in_order = sorted(nodes, key=lambda node: node.id)
        laid_in_order = sorted(laid.laid, key=lambda artifact: artifact.id)
        verdicts: list[Verdict] = [Same("count", len(nodes), len(laid.laid))]
        for i, (node, artifact) in enumerate(zip(answered_in_order, laid_in_order, strict=False)):
            verdicts += self.expected.verdicts(f"[{i}].", node, artifact, self.started)
        return verdicts


@dataclass(frozen=True)
class TheSuperadminSoftDeletesByIds(
    Scenario[TestSeedingSession, ManyArtifactsAndACaller, ArtifactAdapter, Deleted]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-soft-deletes-artifacts-by-ids"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 아티팩트 여럿을 id 목록으로 soft delete 하면, 모두 삭제됨 상태로 온다"

    @override
    def given(self) -> Given[TestSeedingSession, ManyArtifactsAndACaller]:
        return ManyArtifactsAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyArtifactsAndACaller, ArtifactAdapter, Deleted]:
        return SoftDeletingByIds()

    @override
    def then(self) -> Then[ManyArtifactsAndACaller, Deleted]:
        return EveryTargetIsAnswered(
            started=self.started,
            expected=ArtifactLook(availability=ArtifactAvailability.DELETED),
        )


@dataclass(frozen=True)
class AUserWhoIsNotSuperadminMayNotSoftDeleteByIds(
    Scenario[TestSeedingSession, ManyArtifactsAndACaller, ArtifactAdapter, Deleted]
):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-superadmin-may-not-soft-delete-artifacts-by-ids"

    @override
    def describe(self) -> str:
        return (
            "슈퍼관리자가 아닌 사용자는 아티팩트 여럿을 id 목록으로 soft delete 할 수 없고, "
            "역할로 거부된다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyArtifactsAndACaller]:
        return ManyArtifactsAndSomeone()

    @override
    def when(self) -> When[ManyArtifactsAndACaller, ArtifactAdapter, Deleted]:
        return SoftDeletingByIds()

    @override
    def then(self) -> Then[ManyArtifactsAndACaller, Deleted]:
        return TheCallIsRefused(InsufficientPrivilege)


@dataclass(frozen=True)
class TheSuperadminRestoresByIds(
    Scenario[TestSeedingSession, ManyArtifactsAndACaller, ArtifactAdapter, Deleted]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-restores-artifacts-by-ids"

    @override
    def describe(self) -> str:
        return (
            "슈퍼관리자가 soft delete 된 아티팩트 여럿을 id 목록으로 restore 하면, 모두 살아 있는 "
            "상태로 온다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyArtifactsAndACaller]:
        return ManyArtifactsAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyArtifactsAndACaller, ArtifactAdapter, Deleted]:
        return SoftDeletingThenRestoringByIds()

    @override
    def then(self) -> Then[ManyArtifactsAndACaller, Deleted]:
        return EveryTargetIsAnswered(started=self.started, expected=ArtifactLook())


SCENARIOS: list[ArtifactStep] = [
    TheSuperadminSoftDeletesByIds(started=datetime.now(UTC)),
    AUserWhoIsNotSuperadminMayNotSoftDeleteByIds(),
    TheSuperadminRestoresByIds(started=datetime.now(UTC)),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_bulk_deleting(
    scenario: ArtifactStep, adapter: ArtifactAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
