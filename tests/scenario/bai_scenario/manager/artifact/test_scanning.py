"""바깥 레지스트리를 읽는 호출: 스캔, 스캔 위임, 모델 가져오기.

이 셋은 바깥 레지스트리와 저장소에 닿아야 성공하므로, 여기서는 전역 게이트가
권한 없는 호출을 거부하는 것만 확인한다.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.artifact.response import ArtifactNode
from ai.backend.manager.api.adapters.artifact.adapter import ArtifactAdapter
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Says, Scenario, Then, When
from bai_scenario.components.artifact import AnArtifactAndACaller, AnArtifactAndSomeone
from bai_scenario.components.domain import TheCallIsRefused
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type ScanStep = Scenario[
    TestSeedingSession, AnArtifactAndACaller, ArtifactAdapter, list[ArtifactNode]
]


@dataclass(frozen=True)
class Scanning(When[AnArtifactAndACaller, ArtifactAdapter, list[ArtifactNode]]):
    @override
    def operation(self) -> str:
        return "scan"

    @override
    def describe(self, laid: AnArtifactAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 조건 없이 바깥 레지스트리를 스캔합니다",
            english=f"{laid.caller.username} scans the external registries with no condition",
        )

    @override
    async def call(
        self, adapter: ArtifactAdapter, laid: AnArtifactAndACaller
    ) -> list[ArtifactNode]:
        with ActingAs(laid.caller):
            return await adapter.scan(None, None, None, None, None)


@dataclass(frozen=True)
class DelegatingTheScan(When[AnArtifactAndACaller, ArtifactAdapter, list[ArtifactNode]]):
    @override
    def operation(self) -> str:
        return "delegate_scan"

    @override
    def describe(self, laid: AnArtifactAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 조건 없이 바깥 레지스트리 스캔을 위임합니다",
            english=(
                f"{laid.caller.username} delegates a scan of the external registries with no "
                "condition"
            ),
        )

    @override
    async def call(
        self, adapter: ArtifactAdapter, laid: AnArtifactAndACaller
    ) -> list[ArtifactNode]:
        with ActingAs(laid.caller):
            return await adapter.delegate_scan(None, None, None, None, None, None)


@dataclass(frozen=True)
class RetrievingModels(When[AnArtifactAndACaller, ArtifactAdapter, list[ArtifactNode]]):
    @override
    def operation(self) -> str:
        return "retrieve_models"

    @override
    def describe(self, laid: AnArtifactAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 바깥 레지스트리에서 모델 상세를 다시 읽습니다",
            english=f"{laid.caller.username} reads model details again from the external registry",
        )

    @override
    async def call(
        self, adapter: ArtifactAdapter, laid: AnArtifactAndACaller
    ) -> list[ArtifactNode]:
        with ActingAs(laid.caller):
            return await adapter.retrieve_models([], None)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotScan(
    Scenario[TestSeedingSession, AnArtifactAndACaller, ArtifactAdapter, list[ArtifactNode]]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-scan-external-registries"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 바깥 레지스트리를 스캔하려 하면, 전역 역할이 없어 "
            "권한 부족으로 거부됩니다",
            english=(
                "when a user granted nothing tries to scan the external registries, it is "
                "rejected for lack of permission because they hold no global role"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AnArtifactAndACaller]:
        return AnArtifactAndSomeone(role=UserRole.USER)

    @override
    def when(self) -> When[AnArtifactAndACaller, ArtifactAdapter, list[ArtifactNode]]:
        return Scanning()

    @override
    def then(self) -> Then[AnArtifactAndACaller, list[ArtifactNode]]:
        return TheCallIsRefused(InsufficientPrivilege)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotDelegateAScan(
    Scenario[TestSeedingSession, AnArtifactAndACaller, ArtifactAdapter, list[ArtifactNode]]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-delegate-a-scan"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 바깥 레지스트리 스캔을 위임하려 하면, 전역 역할이 없어 "
            "권한 부족으로 거부됩니다",
            english=(
                "when a user granted nothing tries to delegate a scan of the external registries, "
                "it is rejected for lack of permission because they hold no global role"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AnArtifactAndACaller]:
        return AnArtifactAndSomeone(role=UserRole.USER)

    @override
    def when(self) -> When[AnArtifactAndACaller, ArtifactAdapter, list[ArtifactNode]]:
        return DelegatingTheScan()

    @override
    def then(self) -> Then[AnArtifactAndACaller, list[ArtifactNode]]:
        return TheCallIsRefused(InsufficientPrivilege)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotRetrieveModels(
    Scenario[TestSeedingSession, AnArtifactAndACaller, ArtifactAdapter, list[ArtifactNode]]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-retrieve-models"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 바깥 레지스트리에서 모델 상세를 읽으려 하면, 전역 "
            "역할이 없어 권한 부족으로 거부됩니다",
            english=(
                "when a user granted nothing tries to read model details from the external "
                "registry, it is rejected for lack of permission because they hold no global role"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AnArtifactAndACaller]:
        return AnArtifactAndSomeone(role=UserRole.USER)

    @override
    def when(self) -> When[AnArtifactAndACaller, ArtifactAdapter, list[ArtifactNode]]:
        return RetrievingModels()

    @override
    def then(self) -> Then[AnArtifactAndACaller, list[ArtifactNode]]:
        return TheCallIsRefused(InsufficientPrivilege)


SCENARIOS: list[ScanStep] = [
    AUserGrantedNothingMayNotScan(),
    AUserGrantedNothingMayNotDelegateAScan(),
    AUserGrantedNothingMayNotRetrieveModels(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_scanning(
    scenario: ScanStep,
    adapter: ArtifactAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
