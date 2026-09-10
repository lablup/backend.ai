"""복제 맞추기 — 요청은 맞추기를 시작시킬 뿐이고, 누가 시작시킬 수 있는가."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

import pytest
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.deployment import ADeploymentAndACaller, ADeploymentInThatPlace
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

from ai.backend.common.dto.manager.v2.deployment.request import SyncReplicaInput
from ai.backend.common.dto.manager.v2.deployment.response import SyncReplicaPayload
from ai.backend.manager.api.adapters.deployment.adapter import DeploymentAdapter
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.errors.permission import NotEnoughPermission
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

type SyncingStep = Scenario[
    SeedingSession, ADeploymentAndACaller, DeploymentAdapter, SyncReplicaPayload
]


@dataclass(frozen=True)
class Syncing(When[ADeploymentAndACaller, DeploymentAdapter, SyncReplicaPayload]):
    """배포의 복제를 맞추라고 한다."""

    @override
    def operation(self) -> str:
        return "sync_replicas"

    @override
    def describe(self, laid: ADeploymentAndACaller) -> str:
        return f"{laid.caller.username}이 {laid.deployment.metadata.name}의 복제 맞추기를 요청"

    @override
    async def call(
        self, adapter: DeploymentAdapter, laid: ADeploymentAndACaller
    ) -> SyncReplicaPayload:
        with ActingAs(laid.caller):
            return await adapter.sync_replicas(
                SyncReplicaInput(model_deployment_id=laid.deployment.id)
            )


@dataclass(frozen=True)
class SyncingHasStarted(Then[ADeploymentAndACaller, SyncReplicaPayload]):
    """맞추기를 시작했다는 것만 답한다."""

    @override
    def says(self) -> str:
        return "맞추기를 시작했다고 답한다"

    @override
    def look(
        self, laid: ADeploymentAndACaller, answered: Answered[SyncReplicaPayload]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        return [Same("success", payload.success, True)]


@dataclass(frozen=True)
class TheGrantedUserStartsSyncing(
    Scenario[SeedingSession, ADeploymentAndACaller, DeploymentAdapter, SyncReplicaPayload]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-update-starts-syncing-the-replicas"

    @override
    def describe(self) -> str:
        return "수정 권한을 받은 사용자가 복제 맞추기를 요청하면, 맞추기를 시작했다고 답한다"

    @override
    def given(self) -> Given[SeedingSession, ADeploymentAndACaller]:
        return ADeploymentInThatPlace(granted=(Permission.UPDATE,), replica_count=2)

    @override
    def when(self) -> When[ADeploymentAndACaller, DeploymentAdapter, SyncReplicaPayload]:
        return Syncing()

    @override
    def then(self) -> Then[ADeploymentAndACaller, SyncReplicaPayload]:
        return SyncingHasStarted()


@dataclass(frozen=True)
class ReadingIsNotEnoughToSync(
    Scenario[SeedingSession, ADeploymentAndACaller, DeploymentAdapter, SyncReplicaPayload]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-only-read-may-not-sync-the-replicas"

    @override
    def describe(self) -> str:
        return "읽기 권한만 받은 사용자가 복제 맞추기를 요청하면, 권한 부족으로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, ADeploymentAndACaller]:
        return ADeploymentInThatPlace(granted=(Permission.READ,))

    @override
    def when(self) -> When[ADeploymentAndACaller, DeploymentAdapter, SyncReplicaPayload]:
        return Syncing()

    @override
    def then(self) -> Then[ADeploymentAndACaller, SyncReplicaPayload]:
        return TheCallIsRefused(NotEnoughPermission)


SCENARIOS: list[SyncingStep] = [
    TheGrantedUserStartsSyncing(),
    ReadingIsNotEnoughToSync(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_syncing(
    scenario: SyncingStep, adapter: DeploymentAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
