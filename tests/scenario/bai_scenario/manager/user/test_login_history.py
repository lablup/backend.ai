"""로그인 이력 — 누가 누구의 기록을 훑을 수 있는가."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, override

import pytest
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.domain import WAS_HERE, SomeoneOf, WrittenByThisRun
from bai_scenario.components.user import AGrant
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario
from bai_scenario.seeds.domain.domain import SeedDomain
from bai_scenario.seeds.seeder import Laid
from bai_scenario.seeds.user.fields import SeedLoginHistoryOf

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.login_history.request import (
    AdminSearchLoginHistoryInput,
    MySearchLoginHistoryInput,
)
from ai.backend.common.dto.manager.v2.login_history.response import (
    AdminSearchLoginHistoryPayload,
    LoginHistoryNode,
    MySearchLoginHistoryPayload,
)
from ai.backend.manager.api.adapters.login_history.adapter import LoginHistoryAdapter
from ai.backend.manager.data.auth.login_session_types import LoginHistoryData
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    Refused,
    Same,
    SameAs,
    Scenario,
    Then,
    Verdict,
    When,
)

type Answer = AdminSearchLoginHistoryPayload | MySearchLoginHistoryPayload


@dataclass(frozen=True)
class TwoPeopleAndTheirHistory:
    """부르는 사람과 다른 사람, 그리고 둘이 남긴 기록."""

    caller: UserData
    caller_history: LoginHistoryData | None
    other_history: LoginHistoryData | None


class HistoryLayer:
    """사용자 한 명 아래에 그 사용자 도메인의 성공 기록 하나를 심는다."""

    _seeding: SeedingSession

    def __init__(self, seeding: SeedingSession) -> None:
        self._seeding = seeding

    async def history_of(self, user: Laid[UserData]) -> LoginHistoryData:
        record = await self._seeding.adding(
            SeedLoginHistoryOf(domain_name=self._seeding.made(user).domain_name), user
        )
        return self._seeding.made(record)


@dataclass(frozen=True)
class SomeoneAndAnother(Given[Any, TwoPeopleAndTheirHistory]):
    """한 도메인의 사용자 둘. 부르는 사람은 ``permissions``만큼 자기 사용자 권한을 받는다."""

    permissions: tuple[Permission, ...] = ()
    other_has_history: bool = True

    @override
    def describe(self) -> str:
        grant = (
            f"부르는 사람은 자기 사용자에 {', '.join(str(p.name) for p in self.permissions)} 권한을 받았다"
            if self.permissions
            else "부르는 사람은 아무 권한도 받지 않았다"
        )
        return f"도메인 하나와 사용자 둘, {grant}"

    @override
    async def lay(self, seeding: Any) -> TwoPeopleAndTheirHistory:
        layer = HistoryLayer(seeding)
        domain = await seeding.creating(SeedDomain(name_hint="home", description=WAS_HERE))
        caller = await seeding.within(SomeoneOf(domain))
        other = await seeding.within(SomeoneOf(domain))
        caller_history = await layer.history_of(caller)
        other_history = await layer.history_of(other) if self.other_has_history else None
        if self.permissions:
            await seeding.within(AGrant.on_user(caller, caller, *self.permissions))
        return TwoPeopleAndTheirHistory(seeding.made(caller), caller_history, other_history)


@dataclass(frozen=True)
class TheSuperadminAndTwoRecords(Given[Any, TwoPeopleAndTheirHistory]):
    """슈퍼관리자 한 명과, 기록을 하나씩 남긴 사용자 둘."""

    @override
    def describe(self) -> str:
        return "도메인 하나와 슈퍼관리자, 성공 기록을 하나씩 가진 사용자 둘"

    @override
    async def lay(self, seeding: Any) -> TwoPeopleAndTheirHistory:
        layer = HistoryLayer(seeding)
        domain = await seeding.creating(SeedDomain(name_hint="home", description=WAS_HERE))
        first = await seeding.within(SomeoneOf(domain))
        first_history = await layer.history_of(first)
        second = await seeding.within(SomeoneOf(domain))
        second_history = await layer.history_of(second)
        caller = await seeding.within(SomeoneOf(domain, role=UserRole.SUPERADMIN))
        return TwoPeopleAndTheirHistory(seeding.made(caller), second_history, first_history)


@dataclass(frozen=True)
class SomeoneReadingTheDomain(Given[Any, TwoPeopleAndTheirHistory]):
    """도메인 스코프에서 사용자 READ를 받은 사람."""

    @override
    def describe(self) -> str:
        return "도메인 하나, 부르는 사람은 도메인 스코프에서 사용자 READ 권한을 받았다"

    @override
    async def lay(self, seeding: Any) -> TwoPeopleAndTheirHistory:
        domain = await seeding.creating(SeedDomain(name_hint="home", description=WAS_HERE))
        caller = await seeding.within(SomeoneOf(domain))
        await seeding.within(AGrant.on_domain(domain, caller, Permission.READ))
        return TwoPeopleAndTheirHistory(seeding.made(caller), None, None)


@dataclass(frozen=True)
class SearchingEveryRecord(When[TwoPeopleAndTheirHistory, LoginHistoryAdapter, Answer]):
    """페이지 인자 없이 기록 전체를 훑는다."""

    @override
    def operation(self) -> str:
        return "admin_search"

    @override
    def describe(self, laid: TwoPeopleAndTheirHistory) -> str:
        return f"{laid.caller.username}이 로그인 기록 전체를 훑음"

    @override
    async def call(self, adapter: LoginHistoryAdapter, laid: TwoPeopleAndTheirHistory) -> Answer:
        with ActingAs(laid.caller):
            return await adapter.admin_search(AdminSearchLoginHistoryInput())


@dataclass(frozen=True)
class SearchingMyRecords(When[TwoPeopleAndTheirHistory, LoginHistoryAdapter, Answer]):
    """자기 기록을 훑는다."""

    @override
    def operation(self) -> str:
        return "my_search"

    @override
    def describe(self, laid: TwoPeopleAndTheirHistory) -> str:
        return f"{laid.caller.username}이 자기 로그인 기록을 훑음"

    @override
    async def call(self, adapter: LoginHistoryAdapter, laid: TwoPeopleAndTheirHistory) -> Answer:
        with ActingAs(laid.caller):
            return await adapter.my_search(MySearchLoginHistoryInput())


class HistoryNodeLook:
    """기록 노드 하나를 통째로 본다. 기대는 심은 기록에서 온다."""

    _started: datetime

    def __init__(self, started: datetime) -> None:
        self._started = started

    def verdicts(
        self, node: LoginHistoryNode, expected: LoginHistoryData, at: str
    ) -> list[Verdict]:
        return [
            Held(f"{at}id", node.id, SameAs(expected.id, "심은 기록")),
            Held(f"{at}user_id", node.user_id, SameAs(expected.user_id, "기록의 주인")),
            Same(f"{at}domain_name", node.domain_name, expected.domain_name),
            Same(f"{at}result", node.result, "success"),
            Same(f"{at}fail_reason", node.fail_reason, None),
            Same(f"{at}client_ip", node.client_ip, None),
            Held(f"{at}created_at", node.created_at, WrittenByThisRun(self._started)),
        ]


@dataclass(frozen=True)
class EveryRecordInOrder(Then[TwoPeopleAndTheirHistory, Answer]):
    """심은 기록 둘이 순서대로 온다."""

    started: datetime

    @override
    def says(self) -> str:
        return "심은 기록이 모두 순서대로 온다"

    @override
    def look(self, laid: TwoPeopleAndTheirHistory, answered: Answered[Answer]) -> list[Verdict]:
        page = answered.response
        if not isinstance(page, AdminSearchLoginHistoryPayload):
            return [Refused(InsufficientPrivilege, answered.raised)]
        first, second = laid.other_history, laid.caller_history
        assert first is not None and second is not None
        seen: list[Verdict] = [
            Same("total_count", page.total_count, 2),
            Same("has_next_page", page.has_next_page, False),
            Same("has_previous_page", page.has_previous_page, False),
            Same("items.length", len(page.items), 2),
        ]
        if len(page.items) == 2:
            look = HistoryNodeLook(self.started)
            seen.extend(look.verdicts(page.items[0], first, "items[0]."))
            seen.extend(look.verdicts(page.items[1], second, "items[1]."))
        return seen


@dataclass(frozen=True)
class OnlyMyRecord(Then[TwoPeopleAndTheirHistory, Answer]):
    """부르는 사람의 기록 하나만 온다."""

    started: datetime

    @override
    def says(self) -> str:
        return "자기 기록 하나만 온다"

    @override
    def look(self, laid: TwoPeopleAndTheirHistory, answered: Answered[Answer]) -> list[Verdict]:
        page = answered.response
        if not isinstance(page, MySearchLoginHistoryPayload):
            return [Refused(NotEnoughPermission, answered.raised)]
        assert laid.caller_history is not None
        seen: list[Verdict] = [
            Same("total_count", page.total_count, 1),
            Same("has_next_page", page.has_next_page, False),
            Same("has_previous_page", page.has_previous_page, False),
            Same("items.length", len(page.items), 1),
        ]
        if len(page.items) == 1:
            seen.extend(
                HistoryNodeLook(self.started).verdicts(
                    page.items[0], laid.caller_history, "items[0]."
                )
            )
        return seen


type HistoryStep = Scenario[SeedingSession, TwoPeopleAndTheirHistory, LoginHistoryAdapter, Answer]


@dataclass(frozen=True)
class TheSuperadminSearchesEveryRecord(
    Scenario[SeedingSession, TwoPeopleAndTheirHistory, LoginHistoryAdapter, Answer]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-searches-every-users-login-history"

    @override
    def describe(self) -> str:
        return (
            "전역 역할이 문인 이력 검색에서 슈퍼관리자가 훑으면, "
            "사용자와 무관하게 심은 이력이 생성 시각 내림차순으로 온다"
        )

    @override
    def given(self) -> Given[SeedingSession, TwoPeopleAndTheirHistory]:
        return TheSuperadminAndTwoRecords()

    @override
    def when(self) -> When[TwoPeopleAndTheirHistory, LoginHistoryAdapter, Answer]:
        return SearchingEveryRecord()

    @override
    def then(self) -> Then[TwoPeopleAndTheirHistory, Answer]:
        return EveryRecordInOrder(started=self.started)


@dataclass(frozen=True)
class OnlyTheSuperadminSearchesEveryRecord(
    Scenario[SeedingSession, TwoPeopleAndTheirHistory, LoginHistoryAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-may-not-search-every-login-history"

    @override
    def describe(self) -> str:
        return "권한 받은 사용자가 이력 전체 검색을 하려 하면, 전역 역할 문이 막는다"

    @override
    def given(self) -> Given[SeedingSession, TwoPeopleAndTheirHistory]:
        return SomeoneReadingTheDomain()

    @override
    def when(self) -> When[TwoPeopleAndTheirHistory, LoginHistoryAdapter, Answer]:
        return SearchingEveryRecord()

    @override
    def then(self) -> Then[TwoPeopleAndTheirHistory, Answer]:
        return TheCallIsRefused(InsufficientPrivilege)


@dataclass(frozen=True)
class AGrantedUserSearchesOnlyTheirOwnHistory(
    Scenario[SeedingSession, TwoPeopleAndTheirHistory, LoginHistoryAdapter, Answer]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-read-on-themselves-searches-only-their-own-login-history"

    @override
    def describe(self) -> str:
        return "자기 스코프에서 READ를 받은 사용자가 훑으면, 다른 사용자의 이력은 빠진다"

    @override
    def given(self) -> Given[SeedingSession, TwoPeopleAndTheirHistory]:
        return SomeoneAndAnother(permissions=(Permission.READ,))

    @override
    def when(self) -> When[TwoPeopleAndTheirHistory, LoginHistoryAdapter, Answer]:
        return SearchingMyRecords()

    @override
    def then(self) -> Then[TwoPeopleAndTheirHistory, Answer]:
        return OnlyMyRecord(started=self.started)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotSearchTheirHistory(
    Scenario[SeedingSession, TwoPeopleAndTheirHistory, LoginHistoryAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-search-their-own-login-history"

    @override
    def describe(self) -> str:
        return "역할 없이 자기 이력을 훑으려 하면, 본인이어도 스코프 권한 문이 막는다"

    @override
    def given(self) -> Given[SeedingSession, TwoPeopleAndTheirHistory]:
        return SomeoneAndAnother(other_has_history=False)

    @override
    def when(self) -> When[TwoPeopleAndTheirHistory, LoginHistoryAdapter, Answer]:
        return SearchingMyRecords()

    @override
    def then(self) -> Then[TwoPeopleAndTheirHistory, Answer]:
        return TheCallIsRefused(NotEnoughPermission)


SCENARIOS: list[HistoryStep] = [
    TheSuperadminSearchesEveryRecord(started=datetime.now(UTC)),
    OnlyTheSuperadminSearchesEveryRecord(),
    AGrantedUserSearchesOnlyTheirOwnHistory(started=datetime.now(UTC)),
    AUserGrantedNothingMayNotSearchTheirHistory(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_login_history(
    scenario: HistoryStep,
    login_history_adapter: LoginHistoryAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, login_history_adapter, engine)
