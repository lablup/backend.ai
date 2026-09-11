"""폴더 만들기 — 누가 만들 수 있고, 무엇이 채워지는가."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, override

import pytest
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.vfolder.answers import (
    NoAnswer,
    TheFolderBelongsToTheProject,
    look_node,
)
from bai_scenario.components.vfolder.callers import (
    SomeoneGrantedNothing,
    SomeoneGrantedOnAProject,
    SomeoneGrantedOverThemselves,
    SomeoneWhoMadeAFolderThemselves,
    SomeoneWhoseFolderIsGone,
    SomeoneWhoseFolderIsInTheTrash,
)
from bai_scenario.components.vfolder.stage import (
    STORAGE_HOST,
    AFolderAndACaller,
    AFolderMakerAndTheirDomain,
    AProjectAndACaller,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

from ai.backend.common.dto.manager.v2.vfolder.request import (
    CreateVFolderInput,
)
from ai.backend.common.dto.manager.v2.vfolder.response import (
    VFolderNode,
)
from ai.backend.manager.api.adapters.vfolder.adapter import VFolderAdapter
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.errors.storage import VFolderAlreadyExists, VFolderInvalidParameter
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Configured,
    Given,
    Scenario,
    Then,
    Verdict,
    When,
)

ENFORCEMENT = "manager.rbac.enforcement_enabled"

type CreatingStep = Scenario[SeedingSession, Any, VFolderAdapter, VFolderNode]


@dataclass(frozen=True)
class MakingAFolder(When[AFolderMakerAndTheirDomain, VFolderAdapter, VFolderNode]):
    """자기 폴더를 하나 만든다. 호스트를 대지 않으면 설정된 기본 호스트로 간다."""

    named: str
    on_host: str | None = None

    @override
    def operation(self) -> str:
        return "create"

    @override
    def describe(self, laid: AFolderMakerAndTheirDomain) -> str:
        where = f"{self.on_host}에 " if self.on_host else "호스트를 대지 않고 "
        return f"{laid.caller.username}이 {where}{self.named}이라는 폴더를 만듦"

    @override
    async def call(self, adapter: VFolderAdapter, laid: AFolderMakerAndTheirDomain) -> VFolderNode:
        with ActingAs(laid.caller):
            payload = await adapter.create(CreateVFolderInput(name=self.named, host=self.on_host))
        return payload.vfolder


@dataclass(frozen=True)
class MakingAnotherFolder(When[AFolderAndACaller, VFolderAdapter, VFolderNode]):
    """이미 폴더를 가진 사람이 하나를 더 만든다.

    이름을 대지 않으면 이미 가진 폴더의 이름을 쓴다. 그 이름은 시드가 지은 것이므로 행에서
    읽는다.
    """

    named: str | None = None

    @override
    def operation(self) -> str:
        return "create"

    @override
    def describe(self, laid: AFolderAndACaller) -> str:
        return f"{laid.caller.username}이 {self.named or laid.folder.name}이라는 폴더를 만듦"

    @override
    async def call(self, adapter: VFolderAdapter, laid: AFolderAndACaller) -> VFolderNode:
        with ActingAs(laid.caller):
            payload = await adapter.create(
                CreateVFolderInput(name=self.named or laid.folder.name, host=STORAGE_HOST)
            )
        return payload.vfolder


@dataclass(frozen=True)
class MakingAFolderForTheProject(When[AProjectAndACaller, VFolderAdapter, VFolderNode]):
    """프로젝트를 요청에 함께 주고 만든다."""

    named: str

    @override
    def operation(self) -> str:
        return "create"

    @override
    def describe(self, laid: AProjectAndACaller) -> str:
        return f"{laid.caller.username}이 {laid.project.name} 아래 {self.named}이라는 폴더를 만듦"

    @override
    async def call(self, adapter: VFolderAdapter, laid: AProjectAndACaller) -> VFolderNode:
        with ActingAs(laid.caller):
            payload = await adapter.create(
                CreateVFolderInput(name=self.named, host=STORAGE_HOST, project_id=laid.project.id)
            )
        return payload.vfolder


@dataclass(frozen=True)
class TheFolderBelongsToTheMaker(Then[AFolderMakerAndTheirDomain, Any]):
    """만든 폴더가 통째로 오고, 그 주인은 만든 사람이다."""

    started: datetime
    named: str

    @override
    def says(self) -> str:
        return "만든 폴더 전체가 오고, 주인은 만든 사람이다"

    @override
    def look(self, laid: AFolderMakerAndTheirDomain, answered: Answered[Any]) -> list[Verdict]:
        node = answered.response
        if not isinstance(node, VFolderNode):
            return [NoAnswer(answered.raised)]
        return look_node(
            node,
            named=self.named,
            owner=laid.caller.id,
            creator=laid.caller,
            started=self.started,
        )


@dataclass(frozen=True)
class TheFolderTakesTheFreedName(Then[AFolderAndACaller, Any]):
    """앞서 있던 폴더가 쓰던 이름으로 새 폴더가 만들어진다."""

    started: datetime

    @override
    def says(self) -> str:
        return "앞서 있던 폴더의 이름으로 새 폴더가 만들어진다"

    @override
    def look(self, laid: AFolderAndACaller, answered: Answered[Any]) -> list[Verdict]:
        node = answered.response
        if not isinstance(node, VFolderNode):
            return [NoAnswer(answered.raised)]
        return look_node(
            node,
            named=laid.folder.name,
            owner=laid.caller.id,
            creator=laid.caller,
            started=self.started,
        )


@dataclass(frozen=True)
class AGrantedUserMakesOneOfTheirOwn(
    Scenario[SeedingSession, AFolderMakerAndTheirDomain, VFolderAdapter, VFolderNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-granted-user-makes-a-folder-of-their-own"

    @override
    def describe(self) -> str:
        return (
            "자기 스코프에서 폴더를 만들 권한을 받은 사용자가 호스트를 골라 폴더를 만들면, "
            "그 폴더의 주인과 만든 사람이 모두 그 사용자인 폴더 전체가 답으로 온다"
        )

    @override
    def given(self) -> Given[SeedingSession, AFolderMakerAndTheirDomain]:
        return SomeoneGrantedOverThemselves()

    @override
    def when(self) -> When[AFolderMakerAndTheirDomain, VFolderAdapter, VFolderNode]:
        return MakingAFolder(named="work", on_host=STORAGE_HOST)

    @override
    def then(self) -> Then[AFolderMakerAndTheirDomain, VFolderNode]:
        return TheFolderBelongsToTheMaker(started=self.started, named="work")


@dataclass(frozen=True)
class WhatIsLeftOutTakesItsDefault(
    Scenario[SeedingSession, AFolderMakerAndTheirDomain, VFolderAdapter, VFolderNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "leaving-everything-but-the-name-out-takes-the-defaults"

    @override
    def describe(self) -> str:
        return (
            "권한을 받은 사용자가 이름만 주고 폴더를 만들면, 적지 않은 값은 기본값이 되고 "
            "폴더는 설정된 기본 호스트에 놓인다"
        )

    @override
    def given(self) -> Given[SeedingSession, AFolderMakerAndTheirDomain]:
        return SomeoneGrantedOverThemselves()

    @override
    def when(self) -> When[AFolderMakerAndTheirDomain, VFolderAdapter, VFolderNode]:
        return MakingAFolder(named="plain")

    @override
    def then(self) -> Then[AFolderMakerAndTheirDomain, VFolderNode]:
        return TheFolderBelongsToTheMaker(started=self.started, named="plain")


@dataclass(frozen=True)
class AUserGrantedNothingMayNotMakeOne(
    Scenario[SeedingSession, AFolderMakerAndTheirDomain, VFolderAdapter, VFolderNode]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-make-a-folder"

    @override
    def describe(self) -> str:
        return (
            "자기 스코프에 아무 권한도 받지 않은 사용자가 폴더를 만들려 하면, "
            "그 스코프에 걸린 권한이 막아 거부된다"
        )

    @override
    def given(self) -> Given[SeedingSession, AFolderMakerAndTheirDomain]:
        return SomeoneGrantedNothing()

    @override
    def when(self) -> When[AFolderMakerAndTheirDomain, VFolderAdapter, VFolderNode]:
        return MakingAFolder(named="denied", on_host=STORAGE_HOST)

    @override
    def then(self) -> Then[AFolderMakerAndTheirDomain, VFolderNode]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class ANameTheyAlreadyHoldIsRefused(
    Scenario[SeedingSession, AFolderAndACaller, VFolderAdapter, VFolderNode]
):
    @override
    def summary(self) -> str:
        return "a-name-the-caller-already-holds-is-refused"

    @override
    def describe(self) -> str:
        return (
            "권한을 받은 사용자가 자기가 이미 가진 폴더와 같은 이름으로 또 만들려 하면, "
            "이름이 겹친다는 이유로 거부된다"
        )

    @override
    def given(self) -> Given[SeedingSession, AFolderAndACaller]:
        return SomeoneWhoMadeAFolderThemselves()

    @override
    def when(self) -> When[AFolderAndACaller, VFolderAdapter, VFolderNode]:
        return MakingAnotherFolder()

    @override
    def then(self) -> Then[AFolderAndACaller, VFolderNode]:
        return TheCallIsRefused(VFolderAlreadyExists)


@dataclass(frozen=True)
class ANameStillHeldByTheTrashIsRefused(
    Scenario[SeedingSession, AFolderAndACaller, VFolderAdapter, VFolderNode]
):
    @override
    def summary(self) -> str:
        return "a-name-a-trashed-folder-still-holds-is-refused"

    @override
    def describe(self) -> str:
        return (
            "휴지통에 있는 폴더와 같은 이름으로 만들려 하면, 그 폴더가 아직 그 이름을 "
            "쥐고 있으므로 이름이 중복된다는 이유로 거부된다"
        )

    @override
    def given(self) -> Given[SeedingSession, AFolderAndACaller]:
        return SomeoneWhoseFolderIsInTheTrash()

    @override
    def when(self) -> When[AFolderAndACaller, VFolderAdapter, VFolderNode]:
        return MakingAnotherFolder()

    @override
    def then(self) -> Then[AFolderAndACaller, VFolderNode]:
        return TheCallIsRefused(VFolderAlreadyExists)


@dataclass(frozen=True)
class ANameAPurgedFolderLeftBehindIsFree(
    Scenario[SeedingSession, AFolderAndACaller, VFolderAdapter, VFolderNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-name-a-purged-folder-left-behind-can-be-taken-again"

    @override
    def describe(self) -> str:
        return (
            "저장소에서 완전히 사라진 폴더와 같은 이름으로 만들면, 그 이름은 이미 풀려 "
            "있으므로 그 이름을 쓴 새 폴더가 만들어진다"
        )

    @override
    def given(self) -> Given[SeedingSession, AFolderAndACaller]:
        return SomeoneWhoseFolderIsGone()

    @override
    def when(self) -> When[AFolderAndACaller, VFolderAdapter, VFolderNode]:
        return MakingAnotherFolder()

    @override
    def then(self) -> Then[AFolderAndACaller, VFolderNode]:
        return TheFolderTakesTheFreedName(started=self.started)


@dataclass(frozen=True)
class TheFolderAllowanceIsSpent(
    Scenario[SeedingSession, AFolderAndACaller, VFolderAdapter, VFolderNode]
):
    @override
    def summary(self) -> str:
        return "a-caller-who-spent-their-folder-allowance-may-not-make-another"

    @override
    def describe(self) -> str:
        return (
            "자원 정책이 폴더 하나만 허락하는 사용자가 이미 하나를 가진 채 또 만들려 하면, "
            "권한이 아니라 허락된 수를 다 썼다는 이유로 거부된다"
        )

    @override
    def given(self) -> Given[SeedingSession, AFolderAndACaller]:
        return SomeoneWhoMadeAFolderThemselves(max_vfolder_count=1)

    @override
    def when(self) -> When[AFolderAndACaller, VFolderAdapter, VFolderNode]:
        return MakingAnotherFolder(named="one-too-many")

    @override
    def then(self) -> Then[AFolderAndACaller, VFolderNode]:
        return TheCallIsRefused(VFolderInvalidParameter)


@dataclass(frozen=True)
class NamingAProjectMakesItTheOwner(
    Scenario[SeedingSession, AProjectAndACaller, VFolderAdapter, VFolderNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "naming-a-project-in-the-request-makes-the-project-the-owner"

    @override
    def describe(self) -> str:
        return (
            "그 프로젝트에 권한을 받은 사용자가 요청에 프로젝트를 함께 주고 폴더를 만들면, "
            "그 프로젝트가 주인이고 개인 주인은 없는 폴더 전체가 답으로 온다"
        )

    @override
    def given(self) -> Given[SeedingSession, AProjectAndACaller]:
        return SomeoneGrantedOnAProject()

    @override
    def when(self) -> When[AProjectAndACaller, VFolderAdapter, VFolderNode]:
        return MakingAFolderForTheProject(named="shared")

    @override
    def then(self) -> Then[AProjectAndACaller, VFolderNode]:
        return TheFolderBelongsToTheProject(started=self.started, named="shared")


@dataclass(frozen=True)
class EnforcementOffLetsAnyoneMakeOne(
    Scenario[SeedingSession, AFolderMakerAndTheirDomain, VFolderAdapter, VFolderNode], Configured
):
    started: datetime

    @override
    def summary(self) -> str:
        return "turning-enforcement-off-lets-a-user-with-no-grant-make-a-folder"

    @override
    def describe(self) -> str:
        return (
            "권한 집행을 끄면 아무 권한도 받지 않은 사용자도 폴더를 만든다. "
            "만들기를 지키는 것이 역할이 아니라 스코프에 걸린 권한이기 때문이다"
        )

    @override
    def config(self) -> Mapping[str, Any]:
        return {ENFORCEMENT: False}

    @override
    def given(self) -> Given[SeedingSession, AFolderMakerAndTheirDomain]:
        return SomeoneGrantedNothing()

    @override
    def when(self) -> When[AFolderMakerAndTheirDomain, VFolderAdapter, VFolderNode]:
        return MakingAFolder(named="unguarded", on_host=STORAGE_HOST)

    @override
    def then(self) -> Then[AFolderMakerAndTheirDomain, VFolderNode]:
        return TheFolderBelongsToTheMaker(started=self.started, named="unguarded")


SCENARIOS: list[CreatingStep] = [
    AGrantedUserMakesOneOfTheirOwn(started=datetime.now(UTC)),
    WhatIsLeftOutTakesItsDefault(started=datetime.now(UTC)),
    AUserGrantedNothingMayNotMakeOne(),
    ANameTheyAlreadyHoldIsRefused(),
    ANameStillHeldByTheTrashIsRefused(),
    ANameAPurgedFolderLeftBehindIsFree(started=datetime.now(UTC)),
    TheFolderAllowanceIsSpent(),
    NamingAProjectMakesItTheOwner(started=datetime.now(UTC)),
    EnforcementOffLetsAnyoneMakeOne(started=datetime.now(UTC)),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_creating(
    scenario: CreatingStep, adapter: VFolderAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
