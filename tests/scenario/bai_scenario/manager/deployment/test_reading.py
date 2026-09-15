"""배포 읽기 — 누가 어느 배포를 읽을 수 있는가.

없는 것을 가리키는 요청이 슈퍼관리자와 그렇지 않은 사람에게 다른 것으로 거부된다. 권한
검사가 먼저 도는데 없는 행에는 어떤 권한도 걸려 있지 않기 때문이다.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override
from uuid import UUID, uuid4

import pytest
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.deployment import (
    ADeploymentAndACaller,
    ADeploymentInThatPlace,
    AnothersDeploymentAndASuperadmin,
    TheDeploymentNode,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.deployment.response import DeploymentNode, RevisionNode
from ai.backend.manager.api.adapters.deployment.adapter import DeploymentAdapter
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.errors.deployment import DeploymentRevisionNotFound
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.errors.service import EndpointNotFound
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Scenario, Then, When

type ReadingStep = Scenario[
    SeedingSession, ADeploymentAndACaller, DeploymentAdapter, DeploymentNode
]
type RevisionStep = Scenario[SeedingSession, ADeploymentAndACaller, DeploymentAdapter, RevisionNode]


@dataclass(frozen=True)
class ReadingById(When[ADeploymentAndACaller, DeploymentAdapter, DeploymentNode]):
    """id로 읽는다. id를 대지 않으면 심은 배포의 id를 쓴다."""

    named: UUID | None = None

    @override
    def operation(self) -> str:
        return "get"

    @override
    def describe(self, laid: ADeploymentAndACaller) -> str:
        called = (
            "아무것도 갖지 않은 id" if self.named is not None else laid.deployment.metadata.name
        )
        return f"{laid.caller.username}이 {called}로 조회"

    @override
    async def call(self, adapter: DeploymentAdapter, laid: ADeploymentAndACaller) -> DeploymentNode:
        wanted = DeploymentID(self.named) if self.named is not None else laid.deployment.id
        with ActingAs(laid.caller):
            return await adapter.get(wanted)


@dataclass(frozen=True)
class ReadingTheCurrentRevision(When[ADeploymentAndACaller, DeploymentAdapter, RevisionNode]):
    """지금 도는 리비전을 읽는다."""

    @override
    def operation(self) -> str:
        return "get_current_revision"

    @override
    def describe(self, laid: ADeploymentAndACaller) -> str:
        return f"{laid.caller.username}이 {laid.deployment.metadata.name}의 현재 리비전을 조회"

    @override
    async def call(self, adapter: DeploymentAdapter, laid: ADeploymentAndACaller) -> RevisionNode:
        with ActingAs(laid.caller):
            return await adapter.get_current_revision(laid.deployment.id)


@dataclass(frozen=True)
class TheGrantedUserReadsIt(
    Scenario[SeedingSession, ADeploymentAndACaller, DeploymentAdapter, DeploymentNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-read-reads-a-deployment-by-id"

    @override
    def describe(self) -> str:
        return "배포 하나가 있고 읽기 권한을 받은 사용자가 id로 조회하면, 그 배포가 답으로 온다"

    @override
    def given(self) -> Given[SeedingSession, ADeploymentAndACaller]:
        return ADeploymentInThatPlace(granted=(Permission.READ,))

    @override
    def when(self) -> When[ADeploymentAndACaller, DeploymentAdapter, DeploymentNode]:
        return ReadingById()

    @override
    def then(self) -> Then[ADeploymentAndACaller, DeploymentNode]:
        return TheDeploymentNode(started=self.started)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotRead(
    Scenario[SeedingSession, ADeploymentAndACaller, DeploymentAdapter, DeploymentNode]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-read-a-deployment"

    @override
    def describe(self) -> str:
        return "같은 배포가 있고 아무 권한도 받지 않은 사용자가 조회하면, 권한 부족으로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, ADeploymentAndACaller]:
        return ADeploymentInThatPlace()

    @override
    def when(self) -> When[ADeploymentAndACaller, DeploymentAdapter, DeploymentNode]:
        return ReadingById()

    @override
    def then(self) -> Then[ADeploymentAndACaller, DeploymentNode]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AnUnknownIdIsRefusedAsPermission(
    Scenario[SeedingSession, ADeploymentAndACaller, DeploymentAdapter, DeploymentNode]
):
    @override
    def summary(self) -> str:
        return "an-id-nothing-answers-to-is-refused-as-permission-for-a-plain-user"

    @override
    def describe(self) -> str:
        return (
            "읽기 권한을 받은 사용자가 아무것도 갖지 않은 id로 조회하면, 대상이 없다는 것이 "
            "아니라 권한 부족으로 거부된다. 없는 행에는 걸린 권한도 없기 때문이다"
        )

    @override
    def given(self) -> Given[SeedingSession, ADeploymentAndACaller]:
        return ADeploymentInThatPlace(granted=(Permission.READ,))

    @override
    def when(self) -> When[ADeploymentAndACaller, DeploymentAdapter, DeploymentNode]:
        return ReadingById(named=uuid4())

    @override
    def then(self) -> Then[ADeploymentAndACaller, DeploymentNode]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AnUnknownIdIsNotFoundForASuperadmin(
    Scenario[SeedingSession, ADeploymentAndACaller, DeploymentAdapter, DeploymentNode]
):
    @override
    def summary(self) -> str:
        return "an-id-nothing-answers-to-is-not-found-for-a-superadmin"

    @override
    def describe(self) -> str:
        return (
            "슈퍼관리자가 아무것도 갖지 않은 id로 조회하면, 대상이 없다는 것으로 거부된다. "
            "권한 검사를 지나가는 사람만 이 답을 본다"
        )

    @override
    def given(self) -> Given[SeedingSession, ADeploymentAndACaller]:
        return ADeploymentInThatPlace(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ADeploymentAndACaller, DeploymentAdapter, DeploymentNode]:
        return ReadingById(named=uuid4())

    @override
    def then(self) -> Then[ADeploymentAndACaller, DeploymentNode]:
        return TheCallIsRefused(EndpointNotFound)


@dataclass(frozen=True)
class ADeploymentWithNoRevisionHasNoCurrentOne(
    Scenario[SeedingSession, ADeploymentAndACaller, DeploymentAdapter, RevisionNode]
):
    @override
    def summary(self) -> str:
        return "a-deployment-holding-no-revision-answers-nothing-as-its-current-one"

    @override
    def describe(self) -> str:
        return (
            "리비전이 딸리지 않은 배포의 현재 리비전을 조회하면, "
            "현재 리비전이 없다는 이유로 거부된다"
        )

    @override
    def given(self) -> Given[SeedingSession, ADeploymentAndACaller]:
        return ADeploymentInThatPlace(granted=(Permission.READ,))

    @override
    def when(self) -> When[ADeploymentAndACaller, DeploymentAdapter, RevisionNode]:
        return ReadingTheCurrentRevision()

    @override
    def then(self) -> Then[ADeploymentAndACaller, RevisionNode]:
        return TheCallIsRefused(DeploymentRevisionNotFound)


@dataclass(frozen=True)
class TheSuperadminReadsAnothers(
    Scenario[SeedingSession, ADeploymentAndACaller, DeploymentAdapter, DeploymentNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-reads-anothers-deployment-without-a-grant"

    @override
    def describe(self) -> str:
        return (
            "다른 사람이 만든 배포를 아무 권한도 받지 않은 슈퍼관리자가 id로 조회하면, "
            "그 배포가 답으로 온다. 역할이 권한 그래프를 지나간다"
        )

    @override
    def given(self) -> Given[SeedingSession, ADeploymentAndACaller]:
        return AnothersDeploymentAndASuperadmin()

    @override
    def when(self) -> When[ADeploymentAndACaller, DeploymentAdapter, DeploymentNode]:
        return ReadingById()

    @override
    def then(self) -> Then[ADeploymentAndACaller, DeploymentNode]:
        return TheDeploymentNode(started=self.started)


SCENARIOS: list[ReadingStep] = [
    TheGrantedUserReadsIt(started=datetime.now(UTC)),
    TheSuperadminReadsAnothers(started=datetime.now(UTC)),
    AUserGrantedNothingMayNotRead(),
    AnUnknownIdIsRefusedAsPermission(),
    AnUnknownIdIsNotFoundForASuperadmin(),
]

REVISION_SCENARIOS: list[RevisionStep] = [
    ADeploymentWithNoRevisionHasNoCurrentOne(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_reading(
    scenario: ReadingStep, adapter: DeploymentAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)


@pytest.mark.parametrize("scenario", REVISION_SCENARIOS, ids=lambda s: s.summary())
async def test_reading_the_current_revision(
    scenario: RevisionStep, adapter: DeploymentAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
