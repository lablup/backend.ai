"""폴더 여럿의 권한을 한 번에 읽기 — 폴더마다 따로 답한다.

읽을 수 있는 폴더는 받은 비트로, 읽을 수 없는 폴더는 거부로 답하고, 그 거부는 그 폴더를
기다리는 필드에서만 난다.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

import pytest

from ai.backend.common.data.entity.vfolder import VFolderUUID
from ai.backend.common.dto.manager.v2.rbac.types import PermissionBitDTO
from ai.backend.manager.api.adapters.vfolder.adapter import VFolderAdapter
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Scenario, Then, When
from bai_scenario.components.vfolder import (
    MineAnswersItsBitsTheirsIsRefused,
    SomeoneWithTheirOwnFolderBesideAnothers,
    TwoFoldersAndAReaderOfOne,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

type Loaded = list[list[PermissionBitDTO] | Exception]
type LoadingStep = Scenario[SeedingSession, TwoFoldersAndAReaderOfOne, VFolderAdapter, Loaded]


@dataclass(frozen=True)
class LoadingBothFoldersPermissions(When[TwoFoldersAndAReaderOfOne, VFolderAdapter, Loaded]):
    """자기 폴더와 남의 폴더의 권한을 한 번에 읽는다."""

    @override
    def operation(self) -> str:
        return "batch_load_permissions"

    @override
    def describe(self, laid: TwoFoldersAndAReaderOfOne) -> str:
        return f"{laid.caller.username}이 {laid.mine.name}(와)과 {laid.theirs.name}의 권한을 한 번에 읽음"

    @override
    async def call(self, adapter: VFolderAdapter, laid: TwoFoldersAndAReaderOfOne) -> Loaded:
        with ActingAs(laid.caller):
            return await adapter.batch_load_permissions([
                VFolderUUID(laid.mine.id),
                VFolderUUID(laid.theirs.id),
            ])


@dataclass(frozen=True)
class TheOthersFolderIsRefusedAlone(
    Scenario[SeedingSession, TwoFoldersAndAReaderOfOne, VFolderAdapter, Loaded]
):
    @override
    def summary(self) -> str:
        return "loading-permissions-answers-the-own-folder-and-refuses-the-others-alone"

    @override
    def describe(self) -> str:
        return (
            "자기 폴더와 남의 폴더의 권한을 한 번에 읽으면, 자기 폴더는 읽기 비트로, "
            "남의 폴더는 권한 부족의 거부로 답하고 호출 자체는 거부되지 않는다"
        )

    @override
    def given(self) -> Given[SeedingSession, TwoFoldersAndAReaderOfOne]:
        return SomeoneWithTheirOwnFolderBesideAnothers()

    @override
    def when(self) -> When[TwoFoldersAndAReaderOfOne, VFolderAdapter, Loaded]:
        return LoadingBothFoldersPermissions()

    @override
    def then(self) -> Then[TwoFoldersAndAReaderOfOne, Loaded]:
        return MineAnswersItsBitsTheirsIsRefused()


SCENARIOS: list[LoadingStep] = [
    TheOthersFolderIsRefusedAlone(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_loading(
    scenario: LoadingStep, adapter: VFolderAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
