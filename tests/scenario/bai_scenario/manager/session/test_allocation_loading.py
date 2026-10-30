"""세션 여럿의 할당을 id로 한 번에 읽기 — 자리마다 무엇이 오는가."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

import pytest

from ai.backend.common.data.entity.session import SessionID
from ai.backend.common.dto.manager.v2.kernel.response import ResourceAllocationGQLDTO
from ai.backend.manager.api.adapters.session.adapter import SessionAdapter
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
from bai_scenario.components.session import (
    FirstProjectGrant,
    PendingSessionsInTwoProjectsAndACaller,
    PendingSessionsInTwoProjectsAndSomeone,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Answer = list[ResourceAllocationGQLDTO | Exception]
type LoadStep = Scenario[
    TestSeedingSession, PendingSessionsInTwoProjectsAndACaller, SessionAdapter, Answer
]


@dataclass(frozen=True)
class LoadingTheAllocationsOfBothProjects(
    When[PendingSessionsInTwoProjectsAndACaller, SessionAdapter, Answer]
):
    """첫 프로젝트의 세션, 다른 프로젝트의 세션 순으로 할당을 한 번에 읽는다."""

    @override
    def operation(self) -> str:
        return "batch_resource_allocation_by_session"

    @override
    def describe(self, laid: PendingSessionsInTwoProjectsAndACaller) -> str:
        return f"{laid.caller.username}이 두 프로젝트의 대기 세션 할당을 한 번에 읽음"

    @override
    async def call(
        self, adapter: SessionAdapter, laid: PendingSessionsInTwoProjectsAndACaller
    ) -> Answer:
        with ActingAs(laid.caller):
            return await adapter.batch_resource_allocation_by_session([
                SessionID(laid.first_project_session.id),
                SessionID(laid.second_project_session.id),
            ])


@dataclass(frozen=True)
class LoadingTheFirstProjectsAllocation(
    When[PendingSessionsInTwoProjectsAndACaller, SessionAdapter, Answer]
):
    """첫 프로젝트의 세션 하나의 할당만 읽는다."""

    @override
    def operation(self) -> str:
        return "batch_resource_allocation_by_session"

    @override
    def describe(self, laid: PendingSessionsInTwoProjectsAndACaller) -> str:
        return f"{laid.caller.username}이 첫 프로젝트의 대기 세션 할당을 일괄 읽음"

    @override
    async def call(
        self, adapter: SessionAdapter, laid: PendingSessionsInTwoProjectsAndACaller
    ) -> Answer:
        with ActingAs(laid.caller):
            return await adapter.batch_resource_allocation_by_session([
                SessionID(laid.first_project_session.id)
            ])


@dataclass(frozen=True)
class AnEmptyAllocationAlone(Then[PendingSessionsInTwoProjectsAndACaller, Answer]):
    """첫 프로젝트의 세션 하나가 빈 할당으로 온다."""

    @override
    def says(self) -> str:
        return "첫 프로젝트의 세션 하나가 빈 할당으로 온다"

    @override
    def look(
        self, laid: PendingSessionsInTwoProjectsAndACaller, answered: Answered[Answer]
    ) -> list[Verdict]:
        loaded = answered.response
        if loaded is None:
            return [MissingResponse(answered.raised)]
        seen: list[Verdict] = [Same("length", len(loaded), 1)]
        first = loaded[0] if loaded else None
        if isinstance(first, ResourceAllocationGQLDTO):
            seen += [
                Same("[0].requested.entries", first.requested.entries, []),
                Same("[0].used.entries", first.used.entries, []),
                Same("[0].allocated.entries", first.allocated.entries, []),
            ]
        else:
            seen.append(Same("[0]", type(first).__name__, "ResourceAllocationGQLDTO"))
        return seen


@dataclass(frozen=True)
class AnEmptyAllocationThenARefusal(Then[PendingSessionsInTwoProjectsAndACaller, Answer]):
    """첫 프로젝트의 세션은 빈 할당으로, 다른 프로젝트의 세션은 거부로 온다."""

    @override
    def says(self) -> str:
        return "입력 순서대로 첫 프로젝트의 세션은 빈 할당, 다른 프로젝트의 세션은 권한 부족 거부가 온다"

    @override
    def look(
        self, laid: PendingSessionsInTwoProjectsAndACaller, answered: Answered[Answer]
    ) -> list[Verdict]:
        loaded = answered.response
        if loaded is None:
            return [MissingResponse(answered.raised)]
        seen: list[Verdict] = [Same("length", len(loaded), 2)]
        if len(loaded) != 2:
            return seen
        first, second = loaded
        if isinstance(first, ResourceAllocationGQLDTO):
            seen += [
                Same("[0].requested.entries", first.requested.entries, []),
                Same("[0].used.entries", first.used.entries, []),
                Same("[0].allocated.entries", first.allocated.entries, []),
            ]
        else:
            seen.append(Same("[0]", type(first).__name__, "ResourceAllocationGQLDTO"))
        seen.append(Refused(NotEnoughPermission, second if isinstance(second, Exception) else None))
        return seen


@dataclass(frozen=True)
class ARefusalInEachPlace(Then[PendingSessionsInTwoProjectsAndACaller, Answer]):
    """호출은 성공하고, 두 자리 모두 거부로 온다."""

    @override
    def says(self) -> str:
        return "두 자리 모두 권한 부족으로 거부된다"

    @override
    def look(
        self, laid: PendingSessionsInTwoProjectsAndACaller, answered: Answered[Answer]
    ) -> list[Verdict]:
        loaded = answered.response
        if loaded is None:
            return [MissingResponse(answered.raised)]
        seen: list[Verdict] = [Same("length", len(loaded), 2)]
        for answer in loaded:
            seen.append(
                Refused(NotEnoughPermission, answer if isinstance(answer, Exception) else None)
            )
        return seen


@dataclass(frozen=True)
class AProjectReaderLoadsItsSessionsAllocation(
    Scenario[TestSeedingSession, PendingSessionsInTwoProjectsAndACaller, SessionAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-session-read-in-the-project-loads-its-sessions-allocation"

    @override
    def describe(self) -> str:
        return (
            "프로젝트 범위에서 세션 조회 권한을 받은 사용자가 그 프로젝트의 세션 할당을 일괄 읽기로 "
            "읽으면, 할당 행이 없는 그 세션은 빈 할당으로 온다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, PendingSessionsInTwoProjectsAndACaller]:
        return PendingSessionsInTwoProjectsAndSomeone(granted=FirstProjectGrant.SESSION_READ)

    @override
    def when(self) -> When[PendingSessionsInTwoProjectsAndACaller, SessionAdapter, Answer]:
        return LoadingTheFirstProjectsAllocation()

    @override
    def then(self) -> Then[PendingSessionsInTwoProjectsAndACaller, Answer]:
        return AnEmptyAllocationAlone()


@dataclass(frozen=True)
class AProjectReaderLoadsItsSessionAndIsRefusedTheOther(
    Scenario[TestSeedingSession, PendingSessionsInTwoProjectsAndACaller, SessionAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-in-one-project-loads-its-allocation-and-is-refused-the-other"

    @override
    def describe(self) -> str:
        return (
            "한 프로젝트 범위에서만 세션 조회 권한을 받은 사용자가 두 프로젝트의 세션 할당을 한 번에 "
            "읽으면, 입력 순서대로 그 프로젝트의 세션은 빈 할당, 다른 프로젝트의 세션은 권한 부족 "
            "거부가 온다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, PendingSessionsInTwoProjectsAndACaller]:
        return PendingSessionsInTwoProjectsAndSomeone(granted=FirstProjectGrant.SESSION_READ)

    @override
    def when(self) -> When[PendingSessionsInTwoProjectsAndACaller, SessionAdapter, Answer]:
        return LoadingTheAllocationsOfBothProjects()

    @override
    def then(self) -> Then[PendingSessionsInTwoProjectsAndACaller, Answer]:
        return AnEmptyAllocationThenARefusal()


@dataclass(frozen=True)
class AUserGrantedNothingIsRefusedEachAllocation(
    Scenario[TestSeedingSession, PendingSessionsInTwoProjectsAndACaller, SessionAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-gets-a-refusal-in-place-of-each-allocation"

    @override
    def describe(self) -> str:
        return (
            "아무 권한도 받지 않은 사용자가 두 프로젝트의 세션 할당을 한 번에 읽으면, "
            "호출은 성공하되 두 자리 모두 권한 부족으로 거부된다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, PendingSessionsInTwoProjectsAndACaller]:
        return PendingSessionsInTwoProjectsAndSomeone(granted=FirstProjectGrant.NOTHING)

    @override
    def when(self) -> When[PendingSessionsInTwoProjectsAndACaller, SessionAdapter, Answer]:
        return LoadingTheAllocationsOfBothProjects()

    @override
    def then(self) -> Then[PendingSessionsInTwoProjectsAndACaller, Answer]:
        return ARefusalInEachPlace()


SCENARIOS: list[LoadStep] = [
    AProjectReaderLoadsItsSessionsAllocation(),
    AProjectReaderLoadsItsSessionAndIsRefusedTheOther(),
    AUserGrantedNothingIsRefusedEachAllocation(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_allocation_loading(
    scenario: LoadStep, adapter: SessionAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
