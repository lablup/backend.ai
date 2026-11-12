"""세션 여럿 종료."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override
from uuid import UUID

import pytest

from ai.backend.common.dto.manager.v2.common import PartialBulkPayload
from ai.backend.common.dto.manager.v2.session.request import PartialBulkTerminateSessionsInput
from ai.backend.common.dto.manager.v2.session.response import SessionTerminationInfo
from ai.backend.common.dto.manager.v2.session.types import SessionTerminationStatusEnum
from ai.backend.manager.api.adapters.session.adapter import SessionAdapter
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    Language,
    Same,
    SameAs,
    Says,
    Scenario,
    Then,
    Verdict,
    When,
    in_language,
)
from bai_scenario.components.answers import MissingResponse
from bai_scenario.components.domain import Mentions
from bai_scenario.components.session import (
    APendingSessionAndACaller,
    APendingSessionAndSomeone,
    Terminator,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Terminated = PartialBulkPayload[SessionTerminationInfo]
type SessionStep = Scenario[
    TestSeedingSession, APendingSessionAndACaller, SessionAdapter, Terminated
]


@dataclass(frozen=True)
class TerminatingTheSession(When[APendingSessionAndACaller, SessionAdapter, Terminated]):
    """대기 세션을 종료한다. `missing`이 있으면 그 id 도 함께 넣는다."""

    missing: UUID | None = None

    @override
    def operation(self) -> str:
        return "partial_bulk_terminate"

    @override
    def describe(self, laid: APendingSessionAndACaller) -> str:
        besides = (
            Says("과 없는 id 하나", english=" and a missing id") if self.missing is not None else ""
        )
        return Says(
            f"{laid.caller.username}이 대기 세션{besides}를 한 번에 종료합니다",
            english=(
                f"{laid.caller.username} terminates a pending session"
                f"{in_language(besides, Language.ENGLISH)} in one call"
            ),
        )

    @override
    async def call(self, adapter: SessionAdapter, laid: APendingSessionAndACaller) -> Terminated:
        ids: list[UUID] = [laid.session.id]
        if self.missing is not None:
            ids.append(self.missing)
        with ActingAs(laid.caller):
            return await adapter.partial_bulk_terminate(PartialBulkTerminateSessionsInput(ids=ids))


@dataclass(frozen=True)
class TheSessionIsCancelled(Then[APendingSessionAndACaller, Terminated]):
    """대기 세션이 취소됨으로 처리된 목록에 온다. `missing`이 있으면 그 id 는 건너뜀으로 온다."""

    missing: UUID | None = None

    @override
    def says(self) -> str:
        if self.missing is None:
            return Says(
                "대기 세션이 취소됨으로 처리된 목록에 오고, 실패한 것은 없습니다",
                english=(
                    "the pending session comes back in the processed list as cancelled and "
                    "nothing failed"
                ),
            )
        return Says(
            "대기 세션은 취소됨, 없는 id 는 건너뜀으로 처리된 목록에 오고, 실패한 것은 없습니다",
            english=(
                "the pending session comes back as cancelled and the missing id as skipped in "
                "the processed list, and nothing failed"
            ),
        )

    @override
    def look(
        self, laid: APendingSessionAndACaller, answered: Answered[Terminated]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [MissingResponse(answered.raised)]
        expected = 1 if self.missing is None else 2
        verdicts: list[Verdict] = [
            Same("successes count", len(payload.successes), expected),
            Same("failed", payload.failed, []),
        ]
        if payload.successes:
            first = payload.successes[0]
            verdicts += [
                Held[UUID](
                    "successes[0].id",
                    first.id,
                    SameAs(
                        laid.session.id,
                        Says("대기 세션의 id", english="the id of the pending session"),
                    ),
                ),
                Same("successes[0].status", first.status, SessionTerminationStatusEnum.CANCELLED),
            ]
        if self.missing is not None and len(payload.successes) > 1:
            second = payload.successes[1]
            verdicts += [
                Held[UUID](
                    "successes[1].id",
                    second.id,
                    SameAs(
                        self.missing,
                        Says("요청에 넣은 없는 id", english="the missing id given in the request"),
                    ),
                ),
                Same("successes[1].status", second.status, SessionTerminationStatusEnum.SKIPPED),
            ]
        return verdicts


@dataclass(frozen=True)
class NothingIsTerminated(Then[APendingSessionAndACaller, Terminated]):
    """종료된 세션 없이, 대상이 권한 부족 이유로 실패 목록에 온다."""

    @override
    def says(self) -> str:
        return Says(
            "종료된 세션 없이, 대상이 권한이 없다는 이유로 실패 목록에 옵니다",
            english=(
                "no session is terminated and the target comes back in the failed list for "
                "lack of permission"
            ),
        )

    @override
    def look(
        self, laid: APendingSessionAndACaller, answered: Answered[Terminated]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [MissingResponse(answered.raised)]
        verdicts: list[Verdict] = [
            Same("successes", payload.successes, []),
            Same("failed count", len(payload.failed), 1),
        ]
        for failure in payload.failed:
            verdicts += [
                Held[UUID](
                    "failed[0].id",
                    failure.id,
                    SameAs(
                        laid.session.id,
                        Says("대기 세션의 id", english="the id of the pending session"),
                    ),
                ),
                Held("failed[0].message", failure.message, Mentions("Insufficient permission")),
            ]
        return verdicts


@dataclass(frozen=True)
class TerminatingAnswersForTheMissingOne(
    Scenario[TestSeedingSession, APendingSessionAndACaller, SessionAdapter, Terminated]
):
    missing: UUID = UUID(int=1)

    @override
    def summary(self) -> str:
        return "terminating-several-skips-the-missing-one"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 대기 세션과 없는 id 하나를 한 번에 종료하면, 대기 세션은 취소됨, "
            "없는 id 는 건너뜀으로 처리된 목록에 옵니다",
            english=(
                "when the superadmin terminates a pending session and a missing id in one call, "
                "the pending session comes back as cancelled and the missing id as skipped in "
                "the processed list"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, APendingSessionAndACaller]:
        return APendingSessionAndSomeone(who=Terminator.SUPERADMIN)

    @override
    def when(self) -> When[APendingSessionAndACaller, SessionAdapter, Terminated]:
        return TerminatingTheSession(missing=self.missing)

    @override
    def then(self) -> Then[APendingSessionAndACaller, Terminated]:
        return TheSessionIsCancelled(missing=self.missing)


@dataclass(frozen=True)
class AProjectGranteeTerminates(
    Scenario[TestSeedingSession, APendingSessionAndACaller, SessionAdapter, Terminated]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-session-soft-delete-in-the-project-terminates-its-session"

    @override
    def describe(self) -> str:
        return Says(
            "프로젝트 범위에서 세션 soft delete 권한을 받은 사용자가 그 프로젝트의 대기 세션을 "
            "종료하면, 취소됨으로 처리된 목록에 옵니다",
            english=(
                "when a user granted session soft delete in the project scope terminates the "
                "pending session of that project, it comes back as cancelled in the processed "
                "list"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, APendingSessionAndACaller]:
        return APendingSessionAndSomeone(who=Terminator.PROJECT_GRANTEE)

    @override
    def when(self) -> When[APendingSessionAndACaller, SessionAdapter, Terminated]:
        return TerminatingTheSession()

    @override
    def then(self) -> Then[APendingSessionAndACaller, Terminated]:
        return TheSessionIsCancelled()


@dataclass(frozen=True)
class AUserGrantedNothingTerminatesNone(
    Scenario[TestSeedingSession, APendingSessionAndACaller, SessionAdapter, Terminated]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-terminates-none"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 대기 세션을 종료하려 하면, 종료된 것 없이 권한이 "
            "없다는 이유로 실패 목록에 옵니다",
            english=(
                "when a user granted nothing tries to terminate a pending session, none is "
                "terminated and it comes back in the failed list for lack of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, APendingSessionAndACaller]:
        return APendingSessionAndSomeone(who=Terminator.NOBODY_GRANTED)

    @override
    def when(self) -> When[APendingSessionAndACaller, SessionAdapter, Terminated]:
        return TerminatingTheSession()

    @override
    def then(self) -> Then[APendingSessionAndACaller, Terminated]:
        return NothingIsTerminated()


SCENARIOS: list[SessionStep] = [
    TerminatingAnswersForTheMissingOne(),
    AProjectGranteeTerminates(),
    AUserGrantedNothingTerminatesNone(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_partial_bulk_terminating(
    scenario: SessionStep, adapter: SessionAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
