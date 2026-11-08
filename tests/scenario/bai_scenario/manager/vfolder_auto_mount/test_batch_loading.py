"""자동 마운트를 id 로 한 번에 읽기."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override

import pytest

from ai.backend.common.data.entity.vfolder_auto_mount import VFolderAutoMountID
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.dto.manager.v2.vfolder_auto_mount.response import VFolderAutoMountNode
from ai.backend.manager.api.adapters.vfolder_auto_mount.adapter import VFolderAutoMountAdapter
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Refused,
    Same,
    Says,
    Scenario,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.vfolder_auto_mount import (
    AProjectFolderAndAutoMounts,
    AProjectFolderAndSomeone,
    TheAutoMountNode,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Answer = list[VFolderAutoMountNode | Exception | None]
type LoadingStep = Scenario[
    TestSeedingSession, AProjectFolderAndAutoMounts, VFolderAutoMountAdapter, Answer
]


@dataclass(frozen=True)
class LoadingTheAutoMountById(When[AProjectFolderAndAutoMounts, VFolderAutoMountAdapter, Answer]):
    """자동 마운트 id 하나만 준다."""

    @override
    def operation(self) -> str:
        return "bulk_get_ids"

    @override
    def describe(self, laid: AProjectFolderAndAutoMounts) -> str:
        return Says(
            f"{laid.caller.username}이 자동 마운트를 id 로 일괄 조회합니다",
            english=f"{laid.caller.username} loads the auto-mount by id in one call",
        )

    @override
    async def call(
        self, adapter: VFolderAutoMountAdapter, laid: AProjectFolderAndAutoMounts
    ) -> Answer:
        if laid.mount is None:
            raise LookupError("the auto-mount was not seeded")
        with ActingAs(laid.caller):
            return await adapter.bulk_get_ids([VFolderAutoMountID(laid.mount.id)])


@dataclass(frozen=True)
class TheAutoMountAlone(Then[AProjectFolderAndAutoMounts, Answer]):
    """자동 마운트 하나가 통째로 온다."""

    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "자동 마운트 하나가 응답으로 옵니다",
            english="the one auto-mount comes back",
        )

    @override
    def look(self, laid: AProjectFolderAndAutoMounts, answered: Answered[Answer]) -> list[Verdict]:
        loaded = answered.response
        if loaded is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        seen: list[Verdict] = [Same("length", len(loaded), 1)]
        first = loaded[0] if loaded else None
        if isinstance(first, VFolderAutoMountNode):
            seen.extend(TheAutoMountNode(started=self.started).look(laid, Answered(response=first)))
        else:
            seen.append(Same("[0]", type(first).__name__, "VFolderAutoMountNode"))
        return seen


@dataclass(frozen=True)
class ARefusalAlone(Then[AProjectFolderAndAutoMounts, Answer]):
    """호출은 성공하고, 그 자리는 권한 부족으로 거부된다."""

    @override
    def says(self) -> str:
        return Says(
            "그 항목은 권한 부족으로 거부됩니다",
            english="that entry is rejected for lack of permission",
        )

    @override
    def look(self, laid: AProjectFolderAndAutoMounts, answered: Answered[Answer]) -> list[Verdict]:
        loaded = answered.response
        if loaded is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        first = loaded[0] if loaded else None
        return [
            Same("length", len(loaded), 1),
            Refused(NotEnoughPermission, first if isinstance(first, Exception) else None),
        ]


@dataclass(frozen=True)
class AUserGrantedReadLoadsTheAutoMount(
    Scenario[TestSeedingSession, AProjectFolderAndAutoMounts, VFolderAutoMountAdapter, Answer]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-auto-mount-read-loads-it-by-id"

    @override
    def describe(self) -> str:
        return Says(
            "자동 마운트 읽기 권한을 받은 사용자가 그 자동 마운트를 id 로 일괄 조회하면, 그 "
            "자동 마운트가 응답으로 옵니다",
            english=(
                "when a user granted auto-mount read loads it by id, that auto-mount comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AProjectFolderAndAutoMounts]:
        return AProjectFolderAndSomeone(permissions=(Permission.READ,), mounted=True)

    @override
    def when(self) -> When[AProjectFolderAndAutoMounts, VFolderAutoMountAdapter, Answer]:
        return LoadingTheAutoMountById()

    @override
    def then(self) -> Then[AProjectFolderAndAutoMounts, Answer]:
        return TheAutoMountAlone(started=self.started)


@dataclass(frozen=True)
class AUserGrantedNothingGetsARefusal(
    Scenario[TestSeedingSession, AProjectFolderAndAutoMounts, VFolderAutoMountAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-gets-a-rejection-for-an-auto-mount"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 자동 마운트를 id 로 일괄 조회하면, 호출은 성공하되 "
            "그 항목은 권한 부족으로 거부됩니다",
            english=(
                "when a user granted nothing loads an auto-mount by id, the call succeeds but "
                "that entry is rejected for lack of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AProjectFolderAndAutoMounts]:
        return AProjectFolderAndSomeone(mounted=True)

    @override
    def when(self) -> When[AProjectFolderAndAutoMounts, VFolderAutoMountAdapter, Answer]:
        return LoadingTheAutoMountById()

    @override
    def then(self) -> Then[AProjectFolderAndAutoMounts, Answer]:
        return ARefusalAlone()


SCENARIOS: list[LoadingStep] = [
    AUserGrantedReadLoadsTheAutoMount(started=datetime.now(UTC)),
    AUserGrantedNothingGetsARefusal(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_batch_loading(
    scenario: LoadingStep, adapter: VFolderAutoMountAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
