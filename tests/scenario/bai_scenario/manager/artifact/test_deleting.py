"""아티팩트 soft delete, restore."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override

import pytest

from ai.backend.common.data.entity.artifact import ArtifactID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.artifact.response import ArtifactNode
from ai.backend.common.dto.manager.v2.artifact.types import ArtifactAvailability
from ai.backend.manager.api.adapters.artifact.adapter import ArtifactAdapter
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Scenario, Then, When
from bai_scenario.components.artifact import (
    AnArtifactAndACaller,
    AnArtifactAndSomeone,
    ArtifactLook,
    TheArtifactNode,
)
from bai_scenario.components.domain import TheCallIsRefused
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type ArtifactStep = Scenario[
    TestSeedingSession, AnArtifactAndACaller, ArtifactAdapter, ArtifactNode
]


@dataclass(frozen=True)
class SoftDeleting(When[AnArtifactAndACaller, ArtifactAdapter, ArtifactNode]):
    """아티팩트를 soft delete 한다."""

    @override
    def operation(self) -> str:
        return "delete"

    @override
    def describe(self, laid: AnArtifactAndACaller) -> str:
        return f"{laid.caller.username}이 {laid.artifact.name}을 soft delete 함"

    @override
    async def call(self, adapter: ArtifactAdapter, laid: AnArtifactAndACaller) -> ArtifactNode:
        with ActingAs(laid.caller):
            payload = await adapter.delete(ArtifactID(laid.artifact.id))
            return payload.artifact


@dataclass(frozen=True)
class SoftDeletingThenRestoring(When[AnArtifactAndACaller, ArtifactAdapter, ArtifactNode]):
    """soft delete 했다가 restore 한다. restore 의 답을 준다."""

    @override
    def operation(self) -> str:
        return "restore"

    @override
    def describe(self, laid: AnArtifactAndACaller) -> str:
        return f"{laid.caller.username}이 {laid.artifact.name}을 soft delete 했다가 restore 함"

    @override
    async def call(self, adapter: ArtifactAdapter, laid: AnArtifactAndACaller) -> ArtifactNode:
        with ActingAs(laid.caller):
            await adapter.delete(ArtifactID(laid.artifact.id))
            payload = await adapter.restore(ArtifactID(laid.artifact.id))
            return payload.artifact


@dataclass(frozen=True)
class Restoring(When[AnArtifactAndACaller, ArtifactAdapter, ArtifactNode]):
    """restore 한다."""

    @override
    def operation(self) -> str:
        return "restore"

    @override
    def describe(self, laid: AnArtifactAndACaller) -> str:
        return f"{laid.caller.username}이 {laid.artifact.name}을 restore 함"

    @override
    async def call(self, adapter: ArtifactAdapter, laid: AnArtifactAndACaller) -> ArtifactNode:
        with ActingAs(laid.caller):
            payload = await adapter.restore(ArtifactID(laid.artifact.id))
            return payload.artifact


@dataclass(frozen=True)
class TheSuperadminSoftDeletesAnArtifact(
    Scenario[TestSeedingSession, AnArtifactAndACaller, ArtifactAdapter, ArtifactNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-soft-deletes-an-artifact"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 아티팩트를 soft delete 하면, 삭제됨 상태의 아티팩트가 온다"

    @override
    def given(self) -> Given[TestSeedingSession, AnArtifactAndACaller]:
        return AnArtifactAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AnArtifactAndACaller, ArtifactAdapter, ArtifactNode]:
        return SoftDeleting()

    @override
    def then(self) -> Then[AnArtifactAndACaller, ArtifactNode]:
        return TheArtifactNode(
            started=self.started,
            expected=ArtifactLook(availability=ArtifactAvailability.DELETED),
        )


@dataclass(frozen=True)
class AUserGrantedNothingMayNotSoftDelete(
    Scenario[TestSeedingSession, AnArtifactAndACaller, ArtifactAdapter, ArtifactNode]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-soft-delete-an-artifact"

    @override
    def describe(self) -> str:
        return "아무 권한도 받지 않은 사용자는 아티팩트를 soft delete 할 수 없다"

    @override
    def given(self) -> Given[TestSeedingSession, AnArtifactAndACaller]:
        return AnArtifactAndSomeone()

    @override
    def when(self) -> When[AnArtifactAndACaller, ArtifactAdapter, ArtifactNode]:
        return SoftDeleting()

    @override
    def then(self) -> Then[AnArtifactAndACaller, ArtifactNode]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class RestoringBringsItBack(
    Scenario[TestSeedingSession, AnArtifactAndACaller, ArtifactAdapter, ArtifactNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "restoring-brings-an-artifact-back"

    @override
    def describe(self) -> str:
        return "soft delete 된 아티팩트를 restore 하면, 살아 있는 상태의 아티팩트가 온다"

    @override
    def given(self) -> Given[TestSeedingSession, AnArtifactAndACaller]:
        return AnArtifactAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AnArtifactAndACaller, ArtifactAdapter, ArtifactNode]:
        return SoftDeletingThenRestoring()

    @override
    def then(self) -> Then[AnArtifactAndACaller, ArtifactNode]:
        return TheArtifactNode(started=self.started)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotRestore(
    Scenario[TestSeedingSession, AnArtifactAndACaller, ArtifactAdapter, ArtifactNode]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-restore-an-artifact"

    @override
    def describe(self) -> str:
        return "아무 권한도 받지 않은 사용자는 아티팩트를 restore 할 수 없다"

    @override
    def given(self) -> Given[TestSeedingSession, AnArtifactAndACaller]:
        return AnArtifactAndSomeone()

    @override
    def when(self) -> When[AnArtifactAndACaller, ArtifactAdapter, ArtifactNode]:
        return Restoring()

    @override
    def then(self) -> Then[AnArtifactAndACaller, ArtifactNode]:
        return TheCallIsRefused(NotEnoughPermission)


SCENARIOS: list[ArtifactStep] = [
    TheSuperadminSoftDeletesAnArtifact(started=datetime.now(UTC)),
    AUserGrantedNothingMayNotSoftDelete(),
    RestoringBringsItBack(started=datetime.now(UTC)),
    AUserGrantedNothingMayNotRestore(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_deleting(
    scenario: ArtifactStep, adapter: ArtifactAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
