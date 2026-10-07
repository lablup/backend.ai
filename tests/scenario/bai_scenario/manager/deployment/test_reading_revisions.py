"""리비전 읽기 — 소유 배포를 먼저 찾고 그 배포의 권한을 본다.

그 찾기는 없는 id와 볼 수 없는 id를 한 가지로 거부한다. 모든 검사를 지나가는 슈퍼관리자만
대상 없음을 본다. 여럿 집기는 id마다 따로 답한다.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override
from uuid import UUID, uuid4

import pytest

from ai.backend.common.data.entity.deployment_revision import DeploymentRevisionID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.deployment.response import RevisionNode
from ai.backend.manager.api.adapters.deployment.adapter import DeploymentAdapter
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.errors.base.field import FieldNotFoundError
from ai.backend.manager.errors.common import GenericBadRequest
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Scenario, Then, When
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.deployment_revision import (
    ADeploymentToRevise,
    EachNamedRevisionIsAnswered,
    Loaded,
    RevisionsAndACaller,
    RevisionsInTwoProjects,
    TheRevisionNode,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

type ReadingStep = Scenario[SeedingSession, RevisionsAndACaller, DeploymentAdapter, RevisionNode]
type LoadingStep = Scenario[SeedingSession, RevisionsAndACaller, DeploymentAdapter, Loaded]


@dataclass(frozen=True)
class ReadingARevision(When[RevisionsAndACaller, DeploymentAdapter, RevisionNode]):
    """id로 리비전 하나를 읽는다. id를 대지 않으면 심은 첫 리비전을 읽는다."""

    named: UUID | None = None

    @override
    def operation(self) -> str:
        return "get_revision"

    @override
    def describe(self, laid: RevisionsAndACaller) -> str:
        called = (
            "아무것도 갖지 않은 id"
            if self.named is not None
            else f"{laid.deployment.metadata.name}의 첫 리비전 id"
        )
        return f"{laid.caller.username}이 {called}로 리비전을 조회"

    @override
    async def call(self, adapter: DeploymentAdapter, laid: RevisionsAndACaller) -> RevisionNode:
        wanted = self.named if self.named is not None else laid.revisions[0].id
        with ActingAs(laid.caller):
            return await adapter.get_revision(DeploymentRevisionID(wanted))


@dataclass(frozen=True)
class LoadingRevisionsById(When[RevisionsAndACaller, DeploymentAdapter, Loaded]):
    """읽을 수 있는 것, 다른 프로젝트의 것, 없는 id를 차례로 이름 대 한 번에 집는다."""

    @override
    def operation(self) -> str:
        return "batch_load_revisions_by_ids"

    @override
    def describe(self, laid: RevisionsAndACaller) -> str:
        return (
            f"{laid.caller.username}이 {laid.deployment.metadata.name}의 리비전, "
            "다른 프로젝트 배포의 리비전, 아무것도 갖지 않은 id를 차례로 집음"
        )

    @override
    async def call(self, adapter: DeploymentAdapter, laid: RevisionsAndACaller) -> Loaded:
        ids = [laid.revisions[0].id, laid.elsewhere[0].id, uuid4()]
        with ActingAs(laid.caller):
            return await adapter.batch_load_revisions_by_ids([
                DeploymentRevisionID(one) for one in ids
            ])


@dataclass(frozen=True)
class TheGrantedUserReadsIt(
    Scenario[SeedingSession, RevisionsAndACaller, DeploymentAdapter, RevisionNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-read-reads-a-revision-by-id"

    @override
    def describe(self) -> str:
        return "배포 읽기 권한을 받은 사용자가 그 배포의 리비전을 id로 조회하면, 그 리비전이 온다"

    @override
    def given(self) -> Given[SeedingSession, RevisionsAndACaller]:
        return ADeploymentToRevise(granted=(Permission.READ,), revisions=1)

    @override
    def when(self) -> When[RevisionsAndACaller, DeploymentAdapter, RevisionNode]:
        return ReadingARevision()

    @override
    def then(self) -> Then[RevisionsAndACaller, RevisionNode]:
        return TheRevisionNode(started=self.started, number=1, seeded=0)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotReadIt(
    Scenario[SeedingSession, RevisionsAndACaller, DeploymentAdapter, RevisionNode]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-read-a-revision"

    @override
    def describe(self) -> str:
        return (
            "아무 배포 권한도 받지 않은 사용자가 리비전을 id로 조회하면, "
            "키를 풀 수 없다는 이유로 거부된다"
        )

    @override
    def given(self) -> Given[SeedingSession, RevisionsAndACaller]:
        return ADeploymentToRevise(revisions=1)

    @override
    def when(self) -> When[RevisionsAndACaller, DeploymentAdapter, RevisionNode]:
        return ReadingARevision()

    @override
    def then(self) -> Then[RevisionsAndACaller, RevisionNode]:
        return TheCallIsRefused(GenericBadRequest)


@dataclass(frozen=True)
class AnUnknownIdIsRefusedAsUnresolvable(
    Scenario[SeedingSession, RevisionsAndACaller, DeploymentAdapter, RevisionNode]
):
    @override
    def summary(self) -> str:
        return "a-revision-id-nothing-answers-to-is-refused-as-unresolvable"

    @override
    def describe(self) -> str:
        return (
            "배포 읽기 권한을 받은 사용자가 아무것도 갖지 않은 id로 리비전을 조회하면, "
            "볼 수 없는 id와 같은 이유로 거부된다"
        )

    @override
    def given(self) -> Given[SeedingSession, RevisionsAndACaller]:
        return ADeploymentToRevise(granted=(Permission.READ,), revisions=1)

    @override
    def when(self) -> When[RevisionsAndACaller, DeploymentAdapter, RevisionNode]:
        return ReadingARevision(named=uuid4())

    @override
    def then(self) -> Then[RevisionsAndACaller, RevisionNode]:
        return TheCallIsRefused(GenericBadRequest)


@dataclass(frozen=True)
class AnUnknownIdIsNotFoundForASuperadmin(
    Scenario[SeedingSession, RevisionsAndACaller, DeploymentAdapter, RevisionNode]
):
    @override
    def summary(self) -> str:
        return "a-revision-id-nothing-answers-to-is-not-found-for-a-superadmin"

    @override
    def describe(self) -> str:
        return (
            "슈퍼관리자가 아무것도 갖지 않은 id로 리비전을 조회하면, 대상이 없다는 것으로 "
            "거부된다. 모든 검사를 지나가는 사람에게는 감출 것이 없다"
        )

    @override
    def given(self) -> Given[SeedingSession, RevisionsAndACaller]:
        return ADeploymentToRevise(role=UserRole.SUPERADMIN, revisions=1)

    @override
    def when(self) -> When[RevisionsAndACaller, DeploymentAdapter, RevisionNode]:
        return ReadingARevision(named=uuid4())

    @override
    def then(self) -> Then[RevisionsAndACaller, RevisionNode]:
        return TheCallIsRefused(FieldNotFoundError)


@dataclass(frozen=True)
class EachNamedIdIsAnsweredOnItsOwn(
    Scenario[SeedingSession, RevisionsAndACaller, DeploymentAdapter, Loaded]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "loading-revisions-by-id-answers-each-id-on-its-own"

    @override
    def describe(self) -> str:
        return (
            "한 프로젝트에서만 배포 읽기 권한을 받은 사용자가 읽을 수 있는 리비전, 다른 "
            "프로젝트의 리비전, 아무것도 갖지 않은 id를 한 번에 집으면, 이름 댄 순서대로 "
            "리비전, 거부, 빈 자리가 온다"
        )

    @override
    def given(self) -> Given[SeedingSession, RevisionsAndACaller]:
        return RevisionsInTwoProjects(granted=(Permission.READ,))

    @override
    def when(self) -> When[RevisionsAndACaller, DeploymentAdapter, Loaded]:
        return LoadingRevisionsById()

    @override
    def then(self) -> Then[RevisionsAndACaller, Loaded]:
        return EachNamedRevisionIsAnswered(started=self.started)


SCENARIOS: list[ReadingStep] = [
    TheGrantedUserReadsIt(started=datetime.now(UTC)),
    AUserGrantedNothingMayNotReadIt(),
    AnUnknownIdIsRefusedAsUnresolvable(),
    AnUnknownIdIsNotFoundForASuperadmin(),
]

LOADING_SCENARIOS: list[LoadingStep] = [
    EachNamedIdIsAnsweredOnItsOwn(started=datetime.now(UTC)),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_reading_revisions(
    scenario: ReadingStep, adapter: DeploymentAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)


@pytest.mark.parametrize("scenario", LOADING_SCENARIOS, ids=lambda s: s.summary())
async def test_loading_revisions_by_id(
    scenario: LoadingStep, adapter: DeploymentAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
