"""세션을 유휴 검사에서 빼고 다시 넣기."""

from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import Any, override
from uuid import uuid4

import pytest

from ai.backend.common.data.entity.idle_checker import IdleCheckerID
from ai.backend.common.dto.manager.v2.session.request import (
    ExcludeSessionIdleChecksInput,
    IncludeSessionIdleChecksInput,
    SessionIdleCheckTargetInput,
)
from ai.backend.common.dto.manager.v2.session.response import (
    ExcludeSessionIdleChecksPayload,
    IncludeSessionIdleChecksPayload,
)
from ai.backend.manager.api.adapters.session.adapter import SessionAdapter
from ai.backend.manager.data.idle_checker.types import IdleCheckerData
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.data.session.types import SessionEntityData
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.errors.permission import NotEnoughPermission
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
from bai_scenario.components.answers import MissingResponse, TheCallIsRefused
from bai_scenario.components.domain import Mentions, SomeoneOf
from bai_scenario.components.resource_allocation import lay_a_place
from bai_scenario.components.session_reads import SomeoneGrantedSessionIn
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario
from bai_scenario.seeds.idle_checker.checker import TestSeedIdleChecker
from bai_scenario.seeds.session.session import TestSeedSession

type Excluded = ExcludeSessionIdleChecksPayload


class Target(enum.StrEnum):
    """무엇을 검사 대상으로 넘기는지."""

    THE_LAID_PAIR = "the-laid-pair"
    A_CHECKER_THAT_IS_NOT_THERE = "a-checker-that-is-not-there"

    def checker_id(self, laid: ASessionAndAChecker) -> IdleCheckerID:
        if self is Target.A_CHECKER_THAT_IS_NOT_THERE:
            return laid.missing_checker
        return IdleCheckerID(laid.checker.id)

    def says(self) -> Says:
        if self is Target.A_CHECKER_THAT_IS_NOT_THERE:
            return Says(
                "그 세션과 카탈로그에 없는 검사기 하나",
                english="the session and one checker the catalog does not hold",
            )
        return Says("그 세션과 그 검사기", english="the session and the checker")


@dataclass(frozen=True)
class ASessionAndAChecker:
    """대기 세션 하나와 유휴 검사기 하나, 그리고 그것을 부를 사용자."""

    session: SessionEntityData
    checker: IdleCheckerData
    missing_checker: IdleCheckerID
    caller: UserData


@dataclass(frozen=True)
class ASessionWithACheckerAndSomeone(Given[Any, ASessionAndAChecker]):
    """대기 세션 하나와 유휴 검사기 하나, 그리고 정해진 권한을 받은 사용자 한 명."""

    granted: Permission | None = None

    @override
    def describe(self) -> str:
        laid_ko = "대기 세션 하나와 유휴 검사기 하나"
        laid_en = "one pending session and one idle checker"
        if self.granted is None:
            return Says(
                f"{laid_ko}, 그리고 아무 권한도 받지 않은 사용자 한 명",
                english=f"{laid_en}, and one user holding no permission",
            )
        return Says(
            f"{laid_ko}, 그리고 그 프로젝트에서 세션 수정 권한을 받은 사용자 한 명",
            english=(
                f"{laid_en}, and one user granted the session update permission in that project"
            ),
        )

    @override
    async def lay(self, seeding: Any) -> ASessionAndAChecker:
        place = await lay_a_place(seeding, slots=0)
        session = await seeding.creating_from_three(
            TestSeedSession(access_key=place.access_key), place.project, place.owner, place.group
        )
        checker = await seeding.creating(TestSeedIdleChecker())
        if self.granted is None:
            caller = await seeding.within(SomeoneOf(place.domain))
        else:
            caller = await seeding.within(
                SomeoneGrantedSessionIn(
                    place.domain, place.project, self.granted, "session-updater"
                )
            )
        return ASessionAndAChecker(
            session=seeding.made(session),
            checker=seeding.made(checker),
            missing_checker=IdleCheckerID(uuid4()),
            caller=seeding.made(caller),
        )


@dataclass(frozen=True)
class ExcludingThePair(When[ASessionAndAChecker, SessionAdapter, Excluded]):
    target: Target = Target.THE_LAID_PAIR

    @override
    def operation(self) -> str:
        return "exclude_idle_checks"

    @override
    def describe(self, laid: ASessionAndAChecker) -> str:
        said = self.target.says()
        return Says(
            f"{laid.caller.username}이 {said} 를 유휴 검사에서 뺍니다",
            english=(
                f"{laid.caller.username} excludes {in_language(said, Language.ENGLISH)} from idle "
                "checks"
            ),
        )

    @override
    async def call(self, adapter: SessionAdapter, laid: ASessionAndAChecker) -> Excluded:
        with ActingAs(laid.caller):
            return await adapter.exclude_idle_checks(
                ExcludeSessionIdleChecksInput(
                    targets=[
                        SessionIdleCheckTargetInput(
                            checker_id=self.target.checker_id(laid),
                            session_id=laid.session.id,
                        )
                    ]
                )
            )


@dataclass(frozen=True)
class IncludingThePair(
    When[ASessionAndAChecker, SessionAdapter, IncludeSessionIdleChecksPayload]
):
    target: Target = Target.THE_LAID_PAIR

    @override
    def operation(self) -> str:
        return "include_idle_checks"

    @override
    def describe(self, laid: ASessionAndAChecker) -> str:
        said = self.target.says()
        return Says(
            f"{laid.caller.username}이 {said} 를 유휴 검사에 다시 넣습니다",
            english=(
                f"{laid.caller.username} includes {in_language(said, Language.ENGLISH)} in idle "
                "checks again"
            ),
        )

    @override
    async def call(
        self, adapter: SessionAdapter, laid: ASessionAndAChecker
    ) -> IncludeSessionIdleChecksPayload:
        with ActingAs(laid.caller):
            return await adapter.include_idle_checks(
                IncludeSessionIdleChecksInput(
                    targets=[
                        SessionIdleCheckTargetInput(
                            checker_id=self.target.checker_id(laid),
                            session_id=laid.session.id,
                        )
                    ]
                )
            )


def _pair_verdicts(
    laid: ASessionAndAChecker, items: list[Any], failed: list[Any]
) -> list[Verdict]:
    """The one pair the caller named went through and nothing failed."""
    if not items:
        return [Same("items count", len(items), 1), Same("failed count", len(failed), 0)]
    one = items[0]
    return [
        Same("items count", len(items), 1),
        Same("failed count", len(failed), 0),
        Held(
            "items[0].checker_id",
            one.checker_id,
            SameAs(
                IdleCheckerID(laid.checker.id),
                Says("그 검사기의 id", english="the id of the checker"),
            ),
        ),
        Held(
            "items[0].session_id",
            one.session_id,
            SameAs(laid.session.id, Says("그 세션의 id", english="the id of the session")),
        ),
    ]


@dataclass(frozen=True)
class ThePairIsExcluded(Then[ASessionAndAChecker, Excluded]):
    @override
    def says(self) -> str:
        return Says(
            "그 쌍 하나가 빠졌다고 돌아오고, 실패는 없습니다",
            english="the one pair comes back excluded and nothing failed",
        )

    @override
    def look(self, laid: ASessionAndAChecker, answered: Answered[Excluded]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [MissingResponse(answered.raised)]
        return _pair_verdicts(laid, list(payload.items), list(payload.failed))


@dataclass(frozen=True)
class ThePairIsIncluded(Then[ASessionAndAChecker, IncludeSessionIdleChecksPayload]):
    @override
    def says(self) -> str:
        return Says(
            "그 쌍 하나가 다시 들어왔다고 돌아오고, 실패는 없습니다",
            english="the one pair comes back included and nothing failed",
        )

    @override
    def look(
        self, laid: ASessionAndAChecker, answered: Answered[IncludeSessionIdleChecksPayload]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [MissingResponse(answered.raised)]
        return _pair_verdicts(laid, list(payload.items), list(payload.failed))


@dataclass(frozen=True)
class ThePairIsNotExcluded(Then[ASessionAndAChecker, Excluded]):
    @override
    def says(self) -> str:
        return Says(
            "어느 쌍도 빠지지 않고, 부른 그 쌍이 실패 목록에 옵니다",
            english=(
                "no pair is excluded and the one the caller named comes back in the failed list"
            ),
        )

    @override
    def look(self, laid: ASessionAndAChecker, answered: Answered[Excluded]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [MissingResponse(answered.raised)]
        if not payload.failed:
            return [Same("items", list(payload.items), []), Same("failed count", 0, 1)]
        return [
            Same("items", list(payload.items), []),
            Same("failed count", len(payload.failed), 1),
            Held(
                "failed[0].session_id",
                payload.failed[0].session_id,
                SameAs(laid.session.id, Says("그 세션의 id", english="the id of the session")),
            ),
            Held(
                "failed[0].checker_id",
                payload.failed[0].checker_id,
                SameAs(
                    laid.missing_checker,
                    Says("부른 그 검사기의 id", english="the id of the checker named"),
                ),
            ),
            Held("failed[0].message", payload.failed[0].message, Mentions("Idle checker")),
        ]


@dataclass(frozen=True)
class ThePairIsNotIncluded(Then[ASessionAndAChecker, IncludeSessionIdleChecksPayload]):
    @override
    def says(self) -> str:
        return Says(
            "어느 쌍도 다시 들어오지 않고, 부른 그 쌍이 실패 목록에 옵니다",
            english=(
                "no pair is included and the one the caller named comes back in the failed list"
            ),
        )

    @override
    def look(
        self, laid: ASessionAndAChecker, answered: Answered[IncludeSessionIdleChecksPayload]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [MissingResponse(answered.raised)]
        if not payload.failed:
            return [Same("items", list(payload.items), []), Same("failed count", 0, 1)]
        return [
            Same("items", list(payload.items), []),
            Same("failed count", len(payload.failed), 1),
            Held(
                "failed[0].session_id",
                payload.failed[0].session_id,
                SameAs(laid.session.id, Says("그 세션의 id", english="the id of the session")),
            ),
            Held(
                "failed[0].checker_id",
                payload.failed[0].checker_id,
                SameAs(
                    laid.missing_checker,
                    Says("부른 그 검사기의 id", english="the id of the checker named"),
                ),
            ),
            Held("failed[0].message", payload.failed[0].message, Mentions("Idle checker")),
        ]


@dataclass(frozen=True)
class ExcludingAPair(Scenario[TestSeedingSession, ASessionAndAChecker, SessionAdapter, Excluded]):
    granted: Permission | None = None
    target: Target = Target.THE_LAID_PAIR

    @override
    def summary(self) -> str:
        reach = "granted" if self.granted is not None else "granted-nothing"
        return f"excluding-a-pair-from-idle-checks-{reach}-{self.target.value}"

    @override
    def describe(self) -> str:
        if self.granted is None:
            return Says(
                "아무 권한도 받지 않은 사용자가 세션을 유휴 검사에서 빼려 하면, 권한 부족으로 "
                "거부됩니다",
                english=(
                    "when a user granted nothing excludes a session from idle checks, the call is "
                    "rejected for lack of permission"
                ),
            )
        if self.target is Target.A_CHECKER_THAT_IS_NOT_THERE:
            return Says(
                "그 프로젝트에서 세션 수정 권한을 받은 사용자가 없는 검사기로 세션을 빼려 하면, "
                "그 쌍이 실패 목록에 옵니다",
                english=(
                    "when a user granted session update in the project excludes a session with a "
                    "checker the catalog does not hold, that pair comes back in the failed list"
                ),
            )
        return Says(
            "그 프로젝트에서 세션 수정 권한을 받은 사용자가 세션과 검사기 한 쌍을 빼면, 그 쌍이 "
            "빠졌다고 돌아옵니다",
            english=(
                "when a user granted session update in the project excludes one session and "
                "checker pair, that pair comes back excluded"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ASessionAndAChecker]:
        return ASessionWithACheckerAndSomeone(granted=self.granted)

    @override
    def when(self) -> When[ASessionAndAChecker, SessionAdapter, Excluded]:
        return ExcludingThePair(target=self.target)

    @override
    def then(self) -> Then[ASessionAndAChecker, Excluded]:
        if self.granted is None:
            return TheCallIsRefused(NotEnoughPermission)
        if self.target is Target.A_CHECKER_THAT_IS_NOT_THERE:
            return ThePairIsNotExcluded()
        return ThePairIsExcluded()


@dataclass(frozen=True)
class IncludingAPair(
    Scenario[
        TestSeedingSession,
        ASessionAndAChecker,
        SessionAdapter,
        IncludeSessionIdleChecksPayload,
    ]
):
    granted: Permission | None = None
    target: Target = Target.THE_LAID_PAIR

    @override
    def summary(self) -> str:
        reach = "granted" if self.granted is not None else "granted-nothing"
        return f"including-a-pair-in-idle-checks-{reach}-{self.target.value}"

    @override
    def describe(self) -> str:
        if self.granted is None:
            return Says(
                "아무 권한도 받지 않은 사용자가 세션을 유휴 검사에 다시 넣으려 하면, 권한 "
                "부족으로 거부됩니다",
                english=(
                    "when a user granted nothing includes a session in idle checks again, the "
                    "call is rejected for lack of permission"
                ),
            )
        if self.target is Target.A_CHECKER_THAT_IS_NOT_THERE:
            return Says(
                "그 프로젝트에서 세션 수정 권한을 받은 사용자가 없는 검사기로 세션을 다시 넣으려 "
                "하면, 그 쌍이 실패 목록에 옵니다",
                english=(
                    "when a user granted session update in the project includes a session with a "
                    "checker the catalog does not hold, that pair comes back in the failed list"
                ),
            )
        return Says(
            "그 프로젝트에서 세션 수정 권한을 받은 사용자가 세션과 검사기 한 쌍을 다시 넣으면, "
            "그 쌍이 들어왔다고 돌아옵니다",
            english=(
                "when a user granted session update in the project includes one session and "
                "checker pair again, that pair comes back included"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ASessionAndAChecker]:
        return ASessionWithACheckerAndSomeone(granted=self.granted)

    @override
    def when(
        self,
    ) -> When[ASessionAndAChecker, SessionAdapter, IncludeSessionIdleChecksPayload]:
        return IncludingThePair(target=self.target)

    @override
    def then(self) -> Then[ASessionAndAChecker, IncludeSessionIdleChecksPayload]:
        if self.granted is None:
            return TheCallIsRefused(NotEnoughPermission)
        if self.target is Target.A_CHECKER_THAT_IS_NOT_THERE:
            return ThePairIsNotIncluded()
        return ThePairIsIncluded()


SCENARIOS: list[Scenario[Any, Any, Any, Any]] = [
    ExcludingAPair(granted=Permission.UPDATE),
    ExcludingAPair(granted=Permission.UPDATE, target=Target.A_CHECKER_THAT_IS_NOT_THERE),
    ExcludingAPair(),
    IncludingAPair(granted=Permission.UPDATE),
    IncludingAPair(granted=Permission.UPDATE, target=Target.A_CHECKER_THAT_IS_NOT_THERE),
    IncludingAPair(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_idle_checking(
    scenario: Scenario[Any, Any, Any, Any],
    adapter: SessionAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
