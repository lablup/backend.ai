"""로그인 이력 시나리오가 함께 쓰는 전제와 응답 검사."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, override

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.login_history.response import (
    AdminSearchLoginHistoryPayload,
    LoginHistoryNode,
    MySearchLoginHistoryPayload,
)
from ai.backend.manager.data.auth.login_session_types import LoginAttemptResult, LoginHistoryData
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    Language,
    Refused,
    Same,
    SameAs,
    Says,
    Then,
    Verdict,
    in_language,
)
from bai_scenario.components.domain import WAS_HERE, SomeoneOf, WrittenByThisRun
from bai_scenario.components.user import AGrant
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.seeds.domain.domain import TestSeedDomain
from bai_scenario.seeds.seeder import Laid
from bai_scenario.seeds.user.fields import TestSeedLoginHistoryOf

type SearchAnswer = AdminSearchLoginHistoryPayload | MySearchLoginHistoryPayload
type Loaded = list[LoginHistoryNode | Exception | None]

_ADDRESS = "203.0.113.10"


@dataclass(frozen=True)
class HistoryToSearch:
    """호출자와, 요청한 필터와 정렬과 페이지에서 순서대로 돌아와야 하는 기록."""

    caller: UserData
    page: tuple[LoginHistoryData, ...]
    total: int


@dataclass(frozen=True)
class HistoryToLoad:
    """호출자와, 호출자 자신의 기록 둘과 다른 사용자의 기록 하나."""

    caller: UserData
    mine: LoginHistoryData
    also_mine: LoginHistoryData
    theirs: LoginHistoryData


async def record_of(
    seeding: TestSeedingSession,
    user: Laid[UserData],
    result: LoginAttemptResult = LoginAttemptResult.SUCCESS,
) -> LoginHistoryData:
    """사용자 한 명의 로그인 시도 이력 하나. 실패 결과에는 사유와 주소를 함께 심는다."""
    failed = result is not LoginAttemptResult.SUCCESS
    record = await seeding.adding(
        TestSeedLoginHistoryOf(
            domain_name=seeding.made(user).domain_name,
            result=result,
            fail_reason=f"reason of {result.value}" if failed else None,
            client_ip=_ADDRESS if failed else None,
        ),
        user,
    )
    return seeding.made(record)


class HistoryNodeLook:
    """기록 노드 하나를 통째로 본다. 기대는 심은 기록에서 온다."""

    _started: datetime

    def __init__(self, started: datetime) -> None:
        self._started = started

    def verdicts(
        self, node: LoginHistoryNode, expected: LoginHistoryData, at: str
    ) -> list[Verdict]:
        seeded = Says("미리 저장한 기록", english="the record seeded in advance")
        return [
            Held(f"{at}id", node.id, SameAs(expected.id, seeded)),
            Held(f"{at}field_id", node.field_id, SameAs(expected.id, seeded)),
            Held(
                f"{at}user_id",
                node.user_id,
                SameAs(expected.user_id, Says("기록 소유자", english="the record owner")),
            ),
            Same(f"{at}domain_name", node.domain_name, expected.domain_name),
            Same(f"{at}result", node.result.value, expected.result.value),
            Same(f"{at}fail_reason", node.fail_reason, expected.fail_reason),
            Same(f"{at}client_ip", node.client_ip, expected.client_ip),
            Held(f"{at}created_at", node.created_at, WrittenByThisRun(self._started)),
        ]


@dataclass(frozen=True)
class ThePageOfHistory(Then[HistoryToSearch, SearchAnswer]):
    """필터와 정렬과 페이지를 거친 기록이 순서대로 오고, 다음 페이지가 남는다."""

    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "필터에 걸리는 기록 중 정렬 순서의 앞 페이지만 오고, 다음 페이지가 남습니다",
            english=(
                "only the first page of the filtered records in the requested order comes "
                "back, and a next page remains"
            ),
        )

    @override
    def look(self, laid: HistoryToSearch, answered: Answered[SearchAnswer]) -> list[Verdict]:
        page = answered.response
        if page is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        seen: list[Verdict] = [
            Same("total_count", page.total_count, laid.total),
            Same("has_next_page", page.has_next_page, True),
            Same("has_previous_page", page.has_previous_page, False),
            Same("items.length", len(page.items), len(laid.page)),
        ]
        look = HistoryNodeLook(self.started)
        for index, (node, expected) in enumerate(zip(page.items, laid.page, strict=False)):
            seen.extend(look.verdicts(node, expected, f"items[{index}]."))
        return seen


@dataclass(frozen=True)
class AdminHistoryToPage(Given[Any, HistoryToSearch]):
    """superadmin 한 명, 서로 다른 사용자 둘의 이력 네 개."""

    @override
    def describe(self) -> str:
        return Says(
            "도메인 하나와 superadmin 한 명, 사용자 둘이 남긴 이력 넷. 성공 하나, 차단 하나, "
            "자격 증명 오류 하나, 비활성 하나",
            english=(
                "one domain, one superadmin, and four records left by two users: one "
                "success, one blocked, one invalid credentials and one inactive"
            ),
        )

    @override
    async def lay(self, seeding: Any) -> HistoryToSearch:
        domain = await seeding.creating(TestSeedDomain(name_hint="home", description=WAS_HERE))
        first = await seeding.within(SomeoneOf(domain))
        second = await seeding.within(SomeoneOf(domain))
        await record_of(seeding, first)
        blocked = await record_of(seeding, first, LoginAttemptResult.FAILED_BLOCKED)
        invalid = await record_of(seeding, second, LoginAttemptResult.FAILED_INVALID_CREDENTIALS)
        await record_of(seeding, second, LoginAttemptResult.FAILED_USER_INACTIVE)
        caller = await seeding.within(SomeoneOf(domain, role=UserRole.SUPERADMIN))
        return HistoryToSearch(seeding.made(caller), (blocked, invalid), 3)


@dataclass(frozen=True)
class ARegularUserReadingTheDomain(Given[Any, HistoryToSearch]):
    """도메인 스코프에서 사용자 READ 를 받은 일반 사용자."""

    @override
    def describe(self) -> str:
        return Says(
            "도메인 하나와 이력을 남긴 사용자 하나, 호출자는 도메인 스코프에서 사용자 READ "
            "권한을 받은 일반 사용자",
            english=(
                "one domain, one user who left a record, and a regular caller granted the "
                "user READ permission in the domain scope"
            ),
        )

    @override
    async def lay(self, seeding: Any) -> HistoryToSearch:
        domain = await seeding.creating(TestSeedDomain(name_hint="home", description=WAS_HERE))
        other = await seeding.within(SomeoneOf(domain))
        await record_of(seeding, other)
        caller = await seeding.within(SomeoneOf(domain))
        await seeding.within(AGrant.on_domain(domain, caller, Permission.READ))
        return HistoryToSearch(seeding.made(caller), (), 0)


@dataclass(frozen=True)
class MyHistoryToPage(Given[Any, HistoryToSearch]):
    """호출자와 다른 사용자가 남긴 이력. 호출자가 자기 사용자 READ 를 받았는지는 고른다."""

    permitted: bool

    @override
    def describe(self) -> str:
        grant = (
            Says(
                "호출자는 자기 사용자에 READ 권한을 받았습니다",
                english="the caller holds the READ permission on their own user",
            )
            if self.permitted
            else Says(
                "호출자는 아무 권한도 받지 않았습니다",
                english="the caller holds no permission",
            )
        )
        return Says(
            f"도메인 하나와 사용자 둘. 호출자의 이력 넷(성공, 차단, 자격 증명 오류, 비활성)과 "
            f"다른 사용자의 자격 증명 오류 이력 하나, {grant}",
            english=(
                "one domain and two users: four records of the caller (success, blocked, "
                "invalid credentials, inactive), one invalid credentials record of the other "
                f"user, and {in_language(grant, Language.ENGLISH)}"
            ),
        )

    @override
    async def lay(self, seeding: Any) -> HistoryToSearch:
        domain = await seeding.creating(TestSeedDomain(name_hint="home", description=WAS_HERE))
        caller = await seeding.within(SomeoneOf(domain))
        other = await seeding.within(SomeoneOf(domain))
        await record_of(seeding, caller)
        blocked = await record_of(seeding, caller, LoginAttemptResult.FAILED_BLOCKED)
        invalid = await record_of(seeding, caller, LoginAttemptResult.FAILED_INVALID_CREDENTIALS)
        await record_of(seeding, caller, LoginAttemptResult.FAILED_USER_INACTIVE)
        await record_of(seeding, other, LoginAttemptResult.FAILED_INVALID_CREDENTIALS)
        if self.permitted:
            await seeding.within(AGrant.on_user(caller, caller, Permission.READ))
        return HistoryToSearch(seeding.made(caller), (blocked, invalid), 3)


@dataclass(frozen=True)
class HistoryToRead(Given[Any, HistoryToLoad]):
    """호출자 자신의 이력 둘과 다른 사용자의 이력 하나. 호출자는 자기 사용자 READ 를 받는다."""

    @override
    def describe(self) -> str:
        return Says(
            "도메인 하나와 사용자 둘. 호출자는 자기 사용자에 READ 권한을 받았고, 이력은 호출자의 "
            "성공 하나, 호출자의 차단 하나, 다른 사용자의 성공 하나",
            english=(
                "one domain and two users. The caller holds the READ permission on their own "
                "user, and the records are one success and one blocked of the caller, and one "
                "success of the other user"
            ),
        )

    @override
    async def lay(self, seeding: Any) -> HistoryToLoad:
        domain = await seeding.creating(TestSeedDomain(name_hint="home", description=WAS_HERE))
        caller = await seeding.within(SomeoneOf(domain))
        other = await seeding.within(SomeoneOf(domain))
        mine = await record_of(seeding, caller)
        also_mine = await record_of(seeding, caller, LoginAttemptResult.FAILED_BLOCKED)
        theirs = await record_of(seeding, other)
        await seeding.within(AGrant.on_user(caller, caller, Permission.READ))
        return HistoryToLoad(seeding.made(caller), mine, also_mine, theirs)


@dataclass(frozen=True)
class TheSlotsInOrder(Then[HistoryToLoad, Loaded]):
    """요청한 순서대로 항목마다 노드 전체 또는 거부가 온다. 이름은 mine, also_mine, refused."""

    slots: tuple[str, ...]
    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "요청한 순서대로 항목마다 노드 전체 또는 권한 부족이 반환됩니다",
            english="for each item in request order, a whole node or a permission failure comes back",
        )

    @override
    def look(self, laid: HistoryToLoad, answered: Answered[Loaded]) -> list[Verdict]:
        loaded = answered.response
        if loaded is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        by = {"mine": laid.mine, "also_mine": laid.also_mine}
        seen: list[Verdict] = [Same("length", len(loaded), len(self.slots))]
        look = HistoryNodeLook(self.started)
        for index, (got, slot) in enumerate(zip(loaded, self.slots, strict=False)):
            if slot == "refused":
                seen.append(
                    Refused(NotEnoughPermission, got if isinstance(got, Exception) else None)
                )
            elif isinstance(got, LoginHistoryNode):
                seen.extend(look.verdicts(got, by[slot], f"[{index}]."))
            else:
                seen.append(Same(f"[{index}]", type(got).__name__, "LoginHistoryNode"))
        return seen
