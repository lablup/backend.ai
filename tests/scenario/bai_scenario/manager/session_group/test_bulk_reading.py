"""세션 그룹 여럿을 id로 읽기. 자리마다 따로 답한다."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override

import pytest

from ai.backend.common.data.entity.session_group import SessionGroupID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.session_group.response import SessionGroupNode
from ai.backend.manager.api.adapters.session_group.adapter import SessionGroupAdapter
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
from bai_scenario.components.answers import MissingResponse
from bai_scenario.components.session_group import (
    GrantedIn,
    SessionGroupsAndACaller,
    SessionGroupsInTwoProjects,
    UsersGroupLook,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Laid = SessionGroupsAndACaller
type Answers = list[SessionGroupNode | Exception | None]
type BulkReadingStep = Scenario[TestSeedingSession, Laid, SessionGroupAdapter, Answers]


@dataclass(frozen=True)
class ReadingBothGroupsOfTheProject(When[Laid, SessionGroupAdapter, Answers]):
    """사용자가 만든 세션 그룹, 배포의 replica group이 가진 세션 그룹 순으로 여럿 읽는다."""

    @override
    def operation(self) -> str:
        return "bulk_get_ids"

    @override
    def describe(self, laid: Laid) -> str:
        return f"{laid.caller.username}이 사용자가 만든 세션 그룹, 배포의 replica group이 가진 세션 그룹 순으로 여럿 읽기"

    @override
    async def call(self, adapter: SessionGroupAdapter, laid: Laid) -> Answers:
        with ActingAs(laid.caller):
            return await adapter.bulk_get_ids([
                SessionGroupID(laid.users_group.id),
                SessionGroupID(laid.deployment_group.id),
            ])


@dataclass(frozen=True)
class ReadingAMissingId(When[Laid, SessionGroupAdapter, Answers]):
    """아무 세션 그룹도 갖지 않은 id 하나를 여럿 읽기로 읽는다."""

    @override
    def operation(self) -> str:
        return "bulk_get_ids"

    @override
    def describe(self, laid: Laid) -> str:
        return f"{laid.caller.username}이 아무 세션 그룹도 갖지 않은 id로 여럿 읽기"

    @override
    async def call(self, adapter: SessionGroupAdapter, laid: Laid) -> Answers:
        with ActingAs(laid.caller):
            return await adapter.bulk_get_ids([SessionGroupID(uuid.uuid4())])


@dataclass(frozen=True)
class ReadingTheUsersGroupById(When[Laid, SessionGroupAdapter, Answers]):
    """사용자가 만든 세션 그룹 하나를 id 목록으로 읽는다."""

    @override
    def operation(self) -> str:
        return "bulk_get_ids"

    @override
    def describe(self, laid: Laid) -> str:
        return f"{laid.caller.username}이 사용자가 만든 세션 그룹의 id로 여럿 읽기"

    @override
    async def call(self, adapter: SessionGroupAdapter, laid: Laid) -> Answers:
        with ActingAs(laid.caller):
            return await adapter.bulk_get_ids([SessionGroupID(laid.users_group.id)])


@dataclass(frozen=True)
class OnlyTheUsersGroupComesBack(Then[Laid, Answers]):
    """첫 자리에 사용자가 만든 세션 그룹이 오고, 배포의 replica group이 가진 세션 그룹 자리는 비어 있다."""

    started: datetime

    @override
    def says(self) -> str:
        return "첫 자리에 사용자가 만든 세션 그룹 전체가 오고, 배포의 replica group이 가진 세션 그룹 자리는 빈 값이다"

    @override
    def look(self, laid: Laid, answered: Answered[Answers]) -> list[Verdict]:
        answers = answered.response
        if answers is None:
            return [MissingResponse(answered.raised)]
        match answers:
            case [SessionGroupNode() as node, None]:
                return UsersGroupLook(self.started).verdicts("[0].", node, laid)
            case _:
                return [
                    Same(
                        "answers",
                        [type(one).__name__ for one in answers],
                        ["SessionGroupNode", "NoneType"],
                    )
                ]


@dataclass(frozen=True)
class TheOnePlaceIsEmpty(Then[Laid, Answers]):
    """물은 자리 하나가 빈 값으로 온다. 호출 전체는 답한다."""

    @override
    def says(self) -> str:
        return "물은 자리가 빈 값이다"

    @override
    def look(self, laid: Laid, answered: Answered[Answers]) -> list[Verdict]:
        answers = answered.response
        if answers is None:
            return [MissingResponse(answered.raised)]
        return [Same("answers", [type(one).__name__ for one in answers], ["NoneType"])]


@dataclass(frozen=True)
class TheOnePlaceIsRefused(Then[Laid, Answers]):
    """물은 자리 하나가 이 이름으로 거부된다. 호출 전체는 답한다."""

    expected: type[BaseException]

    @override
    def says(self) -> str:
        return "물은 자리가 거부된다"

    @override
    def look(self, laid: Laid, answered: Answered[Answers]) -> list[Verdict]:
        answers = answered.response
        if answers is None:
            return [MissingResponse(answered.raised)]
        match answers:
            case [Exception() as denial]:
                return [Refused(self.expected, denial)]
            case _:
                return [Same("answers", [type(one).__name__ for one in answers], ["거부"])]


@dataclass(frozen=True)
class AGrantedUserReadsBothGroups(
    Scenario[TestSeedingSession, SessionGroupsAndACaller, SessionGroupAdapter, Answers]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-granted-user-bulk-reads-a-users-group-and-a-deployments-group"

    @override
    def describe(self) -> str:
        return (
            "그 프로젝트에서 세션 그룹 읽기 권한을 받은 사용자가 사용자가 만든 세션 그룹과 "
            "배포의 replica group이 가진 세션 그룹을 함께 읽으면, 요청한 순서대로 그 세션 그룹과 빈 값이 온다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, Laid]:
        return SessionGroupsInTwoProjects(granted_in=GrantedIn.THE_PROJECT)

    @override
    def when(self) -> When[Laid, SessionGroupAdapter, Answers]:
        return ReadingBothGroupsOfTheProject()

    @override
    def then(self) -> Then[Laid, Answers]:
        return OnlyTheUsersGroupComesBack(started=self.started)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotBulkRead(
    Scenario[TestSeedingSession, SessionGroupsAndACaller, SessionGroupAdapter, Answers]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-bulk-read-a-session-group"

    @override
    def describe(self) -> str:
        return (
            "아무 권한도 받지 않은 사용자가 사용자가 만든 세션 그룹을 id로 여럿 읽으면, "
            "그 자리가 권한 부족으로 거부된다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, Laid]:
        return SessionGroupsInTwoProjects()

    @override
    def when(self) -> When[Laid, SessionGroupAdapter, Answers]:
        return ReadingTheUsersGroupById()

    @override
    def then(self) -> Then[Laid, Answers]:
        return TheOnePlaceIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class TheSuperadminReadsAMissingId(
    Scenario[TestSeedingSession, SessionGroupsAndACaller, SessionGroupAdapter, Answers]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-bulk-reads-a-missing-id-as-empty"

    @override
    def describe(self) -> str:
        return (
            "슈퍼관리자가 아무 세션 그룹도 갖지 않은 id로 여럿 읽으면, 그 자리가 빈 값으로 온다. "
            "권한 검사를 통과하는 사람이어야 읽기의 답을 볼 수 있어 행위자가 슈퍼관리자다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, Laid]:
        return SessionGroupsInTwoProjects(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[Laid, SessionGroupAdapter, Answers]:
        return ReadingAMissingId()

    @override
    def then(self) -> Then[Laid, Answers]:
        return TheOnePlaceIsEmpty()


SCENARIOS: list[BulkReadingStep] = [
    AGrantedUserReadsBothGroups(started=datetime.now(UTC)),
    AUserGrantedNothingMayNotBulkRead(),
    TheSuperadminReadsAMissingId(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_bulk_reading(
    scenario: BulkReadingStep, adapter: SessionGroupAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
