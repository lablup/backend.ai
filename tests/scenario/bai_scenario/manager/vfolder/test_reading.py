"""폴더 하나 읽기 — 누가 어느 폴더에 닿는가."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, override
from uuid import UUID, uuid4

import pytest
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.vfolder.answers import (
    NoAnswer,
    look_node,
)
from bai_scenario.components.vfolder.callers import (
    SomeoneElsesFolder,
    SomeoneGrantedNothing,
    SomeoneGrantedOverTheDomainWithAFolder,
    SomeoneGrantedOverThemselves,
)
from bai_scenario.components.vfolder.stage import (
    READING,
    AFolderAndACaller,
    AFolderMakerAndTheirDomain,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.vfolder.response import (
    VFolderNode,
)
from ai.backend.manager.api.adapters.vfolder.adapter import VFolderAdapter
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.errors.storage import VFolderNotFound
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Scenario,
    Then,
    Verdict,
    When,
)

type Answer = VFolderNode | list[VFolderNode | None]
type ReadingStep = Scenario[SeedingSession, Any, VFolderAdapter, Answer]


@dataclass(frozen=True)
class ReadingTheFolder(When[AFolderAndACaller, VFolderAdapter, Answer]):
    """서 있는 폴더를 그 id로 읽는다."""

    @override
    def operation(self) -> str:
        return "get"

    @override
    def describe(self, laid: AFolderAndACaller) -> str:
        return f"{laid.caller.username}이 {laid.folder.name}을 id로 조회"

    @override
    async def call(self, adapter: VFolderAdapter, laid: AFolderAndACaller) -> Answer:
        with ActingAs(laid.caller):
            return await adapter.get(laid.folder.id)


@dataclass(frozen=True)
class ReadingAnIdNothingHolds(When[AFolderMakerAndTheirDomain, VFolderAdapter, Answer]):
    """아무 폴더도 갖지 않은 id로 읽는다."""

    missing: UUID

    @override
    def operation(self) -> str:
        return "get"

    @override
    def describe(self, laid: AFolderMakerAndTheirDomain) -> str:
        return f"{laid.caller.username}이 아무 폴더도 갖지 않은 id로 조회"

    @override
    async def call(self, adapter: VFolderAdapter, laid: AFolderMakerAndTheirDomain) -> Answer:
        with ActingAs(laid.caller):
            return await adapter.get(self.missing)


@dataclass(frozen=True)
class TheStandingFolder(Then[AFolderAndACaller, Any]):
    """이미 서 있던 폴더가 심어둔 그대로 온다."""

    started: datetime

    @override
    def says(self) -> str:
        return "심어둔 폴더 전체가 온다"

    @override
    def look(self, laid: AFolderAndACaller, answered: Answered[Any]) -> list[Verdict]:
        node = answered.response
        if not isinstance(node, VFolderNode):
            return [NoAnswer(answered.raised)]
        return look_node(
            node,
            named=laid.folder.name,
            owner=laid.folder.user,
            creator=laid.owner,
            started=self.started,
        )


@dataclass(frozen=True)
class TheOwnerReadsTheirFolder(Scenario[SeedingSession, AFolderAndACaller, VFolderAdapter, Answer]):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-granted-owner-reads-their-own-folder"

    @override
    def describe(self) -> str:
        return (
            "자기 폴더를 읽을 권한을 받은 사용자가 그 폴더를 id로 읽으면, "
            "만들어 둔 그대로의 폴더 전체가 답으로 온다"
        )

    @override
    def given(self) -> Given[SeedingSession, AFolderAndACaller]:
        return SomeoneGrantedOverTheDomainWithAFolder(permissions=READING)

    @override
    def when(self) -> When[AFolderAndACaller, VFolderAdapter, Answer]:
        return ReadingTheFolder()

    @override
    def then(self) -> Then[AFolderAndACaller, Answer]:
        return TheStandingFolder(started=self.started)


@dataclass(frozen=True)
class TheSuperadminReadsSomeoneElsesFolder(
    Scenario[SeedingSession, AFolderAndACaller, VFolderAdapter, Answer]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-reads-a-folder-they-were-granted-nothing-on"

    @override
    def describe(self) -> str:
        return (
            "그 폴더에 아무 권한도 받지 않은 슈퍼관리자가 남이 만든 폴더를 읽으면, "
            "역할이 권한 검사를 지나가 폴더 전체가 답으로 온다"
        )

    @override
    def given(self) -> Given[SeedingSession, AFolderAndACaller]:
        return SomeoneElsesFolder(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AFolderAndACaller, VFolderAdapter, Answer]:
        return ReadingTheFolder()

    @override
    def then(self) -> Then[AFolderAndACaller, Answer]:
        return TheStandingFolder(started=self.started)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotReadIt(
    Scenario[SeedingSession, AFolderAndACaller, VFolderAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-read-someone-elses-folder"

    @override
    def describe(self) -> str:
        return (
            "남의 폴더에 아무 권한도 받지 않은 사용자가 그것을 읽으려 하면, "
            "그 폴더에 걸린 권한이 막아 거부된다"
        )

    @override
    def given(self) -> Given[SeedingSession, AFolderAndACaller]:
        return SomeoneElsesFolder()

    @override
    def when(self) -> When[AFolderAndACaller, VFolderAdapter, Answer]:
        return ReadingTheFolder()

    @override
    def then(self) -> Then[AFolderAndACaller, Answer]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AnIdNothingHoldsLooksLikeNoPermission(
    Scenario[SeedingSession, AFolderMakerAndTheirDomain, VFolderAdapter, Answer]
):
    missing: UUID

    @override
    def summary(self) -> str:
        return "an-id-nothing-holds-is-refused-as-a-missing-permission"

    @override
    def describe(self) -> str:
        return (
            "읽기 권한을 받은 사용자가 아무 폴더도 갖지 않은 id로 조회하면, "
            "대상이 없다는 것이 아니라 권한 부족으로 거부된다. 없는 행에는 걸린 권한도 없다"
        )

    @override
    def given(self) -> Given[SeedingSession, AFolderMakerAndTheirDomain]:
        return SomeoneGrantedOverThemselves(permissions=READING)

    @override
    def when(self) -> When[AFolderMakerAndTheirDomain, VFolderAdapter, Answer]:
        return ReadingAnIdNothingHolds(missing=self.missing)

    @override
    def then(self) -> Then[AFolderMakerAndTheirDomain, Answer]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class OnlyTheSuperadminSeesItIsMissing(
    Scenario[SeedingSession, AFolderMakerAndTheirDomain, VFolderAdapter, Answer]
):
    missing: UUID

    @override
    def summary(self) -> str:
        return "only-the-superadmin-is-told-the-folder-is-not-there"

    @override
    def describe(self) -> str:
        return (
            "슈퍼관리자가 아무 폴더도 갖지 않은 id로 조회하면, "
            "권한 검사를 지나가므로 대상이 없다는 것으로 거부된다"
        )

    @override
    def given(self) -> Given[SeedingSession, AFolderMakerAndTheirDomain]:
        return SomeoneGrantedNothing(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AFolderMakerAndTheirDomain, VFolderAdapter, Answer]:
        return ReadingAnIdNothingHolds(missing=self.missing)

    @override
    def then(self) -> Then[AFolderMakerAndTheirDomain, Answer]:
        return TheCallIsRefused(VFolderNotFound)


_MISSING = uuid4()

SCENARIOS: list[ReadingStep] = [
    TheOwnerReadsTheirFolder(started=datetime.now(UTC)),
    TheSuperadminReadsSomeoneElsesFolder(started=datetime.now(UTC)),
    AUserGrantedNothingMayNotReadIt(),
    AnIdNothingHoldsLooksLikeNoPermission(missing=_MISSING),
    OnlyTheSuperadminSeesItIsMissing(missing=_MISSING),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_reading(
    scenario: ReadingStep, adapter: VFolderAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
