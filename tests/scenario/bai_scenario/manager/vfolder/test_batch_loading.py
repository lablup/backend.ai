"""id 여러 개를 한 번에 읽기 — 답이 준 순서를 지키는가."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override
from uuid import UUID, uuid4

import pytest
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.vfolder.answers import (
    NoAnswer,
)
from bai_scenario.components.vfolder.callers import (
    FoldersOfTwoOthers,
    SomeoneGrantedNothing,
    SomeoneGrantedOverTheDomainWithAFolder,
)
from bai_scenario.components.vfolder.stage import (
    READING,
    AFolderAndACaller,
    AFolderMakerAndTheirDomain,
    FoldersAndACaller,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

from ai.backend.common.data.entity.vfolder import VFolderUUID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.vfolder.response import (
    VFolderNode,
)
from ai.backend.manager.api.adapters.vfolder.adapter import VFolderAdapter
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Same,
    Scenario,
    Then,
    Verdict,
    When,
)

type Answer = VFolderNode | list[VFolderNode | None]
type ReadingStep = Scenario[SeedingSession, Any, VFolderAdapter, Answer]


@dataclass(frozen=True)
class PickingThemAllAtOnce(When[FoldersAndACaller, VFolderAdapter, Answer]):
    """서 있는 폴더들과 아무것도 갖지 않은 id 하나를 함께 준다."""

    missing: UUID

    @override
    def operation(self) -> str:
        return "batch_load_by_ids"

    @override
    def describe(self, laid: FoldersAndACaller) -> str:
        return f"{laid.caller.username}이 폴더 {len(laid.seen)}개와 없는 id 하나를 함께 조회"

    @override
    async def call(self, adapter: VFolderAdapter, laid: FoldersAndACaller) -> Answer:
        with ActingAs(laid.caller):
            return await adapter.batch_load_by_ids([
                *(VFolderUUID(one.id) for one in laid.seen),
                VFolderUUID(self.missing),
            ])


@dataclass(frozen=True)
class PickingTheirOwnById(When[AFolderAndACaller, VFolderAdapter, Answer]):
    """자기 폴더 id 하나만 준다."""

    @override
    def operation(self) -> str:
        return "batch_load_by_ids"

    @override
    def describe(self, laid: AFolderAndACaller) -> str:
        return f"{laid.caller.username}이 자기 폴더 id로 조회"

    @override
    async def call(self, adapter: VFolderAdapter, laid: AFolderAndACaller) -> Answer:
        with ActingAs(laid.caller):
            return await adapter.batch_load_by_ids([VFolderUUID(laid.folder.id)])


@dataclass(frozen=True)
class PickingNothing(When[AFolderMakerAndTheirDomain, VFolderAdapter, Answer]):
    """빈 목록을 준다."""

    @override
    def operation(self) -> str:
        return "batch_load_by_ids"

    @override
    def describe(self, laid: AFolderMakerAndTheirDomain) -> str:
        return f"{laid.caller.username}이 빈 목록으로 조회"

    @override
    async def call(self, adapter: VFolderAdapter, laid: AFolderMakerAndTheirDomain) -> Answer:
        with ActingAs(laid.caller):
            return await adapter.batch_load_by_ids([])


@dataclass(frozen=True)
class NothingComesBack(Then[Any, Answer]):
    """빈 목록을 주면 빈 목록이 온다."""

    @override
    def says(self) -> str:
        return "답이 비어 있다"

    @override
    def look(self, laid: Any, answered: Answered[Answer]) -> list[Verdict]:
        return [Same("답", answered.response, [])]


@dataclass(frozen=True)
class TheListKeepsTheOrder(Then[FoldersAndACaller, Any]):
    """준 순서 그대로 오고, 아무것도 갖지 않은 자리는 비어 온다."""

    asked: int
    missing_at: int

    @override
    def says(self) -> str:
        return "준 순서 그대로 오고, 없는 id 자리는 비어서 온다"

    @override
    def look(self, laid: FoldersAndACaller, answered: Answered[Any]) -> list[Verdict]:
        got = answered.response
        if not isinstance(got, list):
            return [NoAnswer(answered.raised)]
        return [
            Same("길이", len(got), self.asked),
            Same("없는 id 자리", got[self.missing_at], None),
            Same(
                "찾은 것",
                [one.metadata.name for one in got if one is not None],
                [one.name for one in laid.seen],
            ),
        ]


@dataclass(frozen=True)
class TheListKeepsWhatWasAsked(Scenario[SeedingSession, FoldersAndACaller, VFolderAdapter, Answer]):
    missing: UUID

    @override
    def summary(self) -> str:
        return "picking-several-ids-keeps-the-order-and-leaves-a-gap"

    @override
    def describe(self) -> str:
        return (
            "슈퍼관리자가 서 있는 폴더들과 아무것도 갖지 않은 id를 섞어 주면, "
            "준 순서 그대로 오고 없는 자리는 비어서 온다"
        )

    @override
    def given(self) -> Given[SeedingSession, FoldersAndACaller]:
        return FoldersOfTwoOthers(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[FoldersAndACaller, VFolderAdapter, Answer]:
        return PickingThemAllAtOnce(missing=self.missing)

    @override
    def then(self) -> Then[FoldersAndACaller, Answer]:
        return TheListKeepsTheOrder(asked=3, missing_at=2)


@dataclass(frozen=True)
class APlainUserMayNotPickByIds(
    Scenario[SeedingSession, AFolderAndACaller, VFolderAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-may-not-pick-folders-by-ids"

    @override
    def describe(self) -> str:
        return (
            "슈퍼관리자가 아닌 사용자가 자기 폴더의 id를 주더라도, "
            "이 조회는 권한이 아니라 역할이 지키므로 거부된다"
        )

    @override
    def given(self) -> Given[SeedingSession, AFolderAndACaller]:
        return SomeoneGrantedOverTheDomainWithAFolder(permissions=READING)

    @override
    def when(self) -> When[AFolderAndACaller, VFolderAdapter, Answer]:
        return PickingTheirOwnById()

    @override
    def then(self) -> Then[AFolderAndACaller, Answer]:
        return TheCallIsRefused(InsufficientPrivilege)


@dataclass(frozen=True)
class AnEmptyListIsAnsweredToAnyone(
    Scenario[SeedingSession, AFolderMakerAndTheirDomain, VFolderAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "an-empty-list-of-ids-is-answered-before-anything-is-checked"

    @override
    def describe(self) -> str:
        return "아무 권한도 받지 않은 사용자가 빈 id 목록을 주면, 검사에 닿기 전에 빈 답으로 끝난다"

    @override
    def given(self) -> Given[SeedingSession, AFolderMakerAndTheirDomain]:
        return SomeoneGrantedNothing()

    @override
    def when(self) -> When[AFolderMakerAndTheirDomain, VFolderAdapter, Answer]:
        return PickingNothing()

    @override
    def then(self) -> Then[AFolderMakerAndTheirDomain, Answer]:
        return NothingComesBack()


_MISSING = uuid4()

SCENARIOS: list[ReadingStep] = [
    TheListKeepsWhatWasAsked(missing=_MISSING),
    APlainUserMayNotPickByIds(),
    AnEmptyListIsAnsweredToAnyone(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_batch_loading(
    scenario: ReadingStep, adapter: VFolderAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
