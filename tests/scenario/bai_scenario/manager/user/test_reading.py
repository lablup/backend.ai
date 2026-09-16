"""사용자 읽기 — 하나를 읽을 때와 여럿을 한 번에 읽을 때."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, override
from uuid import uuid4

import pytest

from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.user.response import UserNode
from ai.backend.manager.api.adapters.user.adapter import UserAdapter
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.data.user.types import UserData
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
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.domain import WAS_HERE, SomeoneOf
from bai_scenario.components.user import AGrant, UserNodeLook
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario
from bai_scenario.seeds.domain.domain import SeedDomain

type Loaded = list[UserNode | Exception | None]
type Answer = UserNode | Loaded


@dataclass(frozen=True)
class AReaderAndATarget:
    """읽을 사람과 읽힐 사람."""

    caller: UserData
    target: UserData


@dataclass(frozen=True)
class AReaderAndTwoUsers:
    """읽을 사람과, 그 사람이 읽을 수 있는 사람, 읽을 수 없는 사람."""

    caller: UserData
    readable: UserData
    unreadable: UserData


@dataclass(frozen=True)
class SomeoneAndAnother(Given[Any, AReaderAndATarget]):
    """한 도메인의 사용자 둘. `granted`면 부르는 사람이 상대 사용자에 READ를 받는다."""

    granted: bool
    role: UserRole = UserRole.USER

    @override
    def describe(self) -> str:
        if self.granted:
            return "도메인 하나와 사용자 둘, 한 사람은 다른 사람에 대한 사용자 읽기 권한을 받았다"
        return "도메인 하나와 사용자 둘, 아무도 권한을 받지 않았다"

    @override
    async def lay(self, seeding: Any) -> AReaderAndATarget:
        domain = await seeding.creating(SeedDomain(name_hint="home", description=WAS_HERE))
        target = await seeding.within(SomeoneOf(domain))
        caller = await seeding.within(SomeoneOf(domain, role=self.role))
        if self.granted:
            await seeding.within(AGrant.on_user(target, caller, Permission.READ))
        return AReaderAndATarget(seeding.made(caller), seeding.made(target))


@dataclass(frozen=True)
class SomeoneReadingOneOfTwo(Given[Any, AReaderAndTwoUsers]):
    """한 도메인의 사용자 셋. 부르는 사람은 둘 중 한 사람에게만 READ를 받았다."""

    @override
    def describe(self) -> str:
        return "도메인 하나와 사용자 셋, 부르는 사람은 한 사람에 대한 사용자 읽기 권한만 받았다"

    @override
    async def lay(self, seeding: Any) -> AReaderAndTwoUsers:
        domain = await seeding.creating(SeedDomain(name_hint="home", description=WAS_HERE))
        readable = await seeding.within(SomeoneOf(domain))
        unreadable = await seeding.within(SomeoneOf(domain))
        caller = await seeding.within(SomeoneOf(domain))
        await seeding.within(AGrant.on_user(readable, caller, Permission.READ))
        return AReaderAndTwoUsers(
            seeding.made(caller), seeding.made(readable), seeding.made(unreadable)
        )


@dataclass(frozen=True)
class ReadingTheTarget(When[AReaderAndATarget, UserAdapter, Answer]):
    """상대 사용자를 id로 읽는다."""

    @override
    def operation(self) -> str:
        return "get"

    @override
    def describe(self, laid: AReaderAndATarget) -> str:
        return f"{laid.caller.username}이 {laid.target.username}을 읽음"

    @override
    async def call(self, adapter: UserAdapter, laid: AReaderAndATarget) -> Answer:
        with ActingAs(laid.caller):
            payload = await adapter.get(laid.target.id)
        return payload.user


@dataclass(frozen=True)
class LoadingReadableUnreadableAndMissing(When[AReaderAndTwoUsers, UserAdapter, Answer]):
    """읽을 수 있는 사람, 읽을 수 없는 사람, 없는 id 순으로 한 번에 읽는다."""

    @override
    def operation(self) -> str:
        return "batch_load_by_ids"

    @override
    def describe(self, laid: AReaderAndTwoUsers) -> str:
        return (
            f"{laid.caller.username}이 {laid.readable.username}, "
            f"{laid.unreadable.username}, 없는 id 순으로 일괄 읽음"
        )

    @override
    async def call(self, adapter: UserAdapter, laid: AReaderAndTwoUsers) -> Answer:
        with ActingAs(laid.caller):
            return await adapter.batch_load_by_ids([
                UserID(laid.readable.id),
                UserID(laid.unreadable.id),
                UserID(uuid4()),
            ])


@dataclass(frozen=True)
class LoadingTheTargetAndMissing(When[AReaderAndATarget, UserAdapter, Answer]):
    """있는 사람과 없는 id를 한 번에 읽는다."""

    @override
    def operation(self) -> str:
        return "batch_load_by_ids"

    @override
    def describe(self, laid: AReaderAndATarget) -> str:
        return f"{laid.caller.username}이 {laid.target.username}과 없는 id를 일괄 읽음"

    @override
    async def call(self, adapter: UserAdapter, laid: AReaderAndATarget) -> Answer:
        with ActingAs(laid.caller):
            return await adapter.batch_load_by_ids([UserID(laid.target.id), UserID(uuid4())])


@dataclass(frozen=True)
class LoadingNothing(When[AReaderAndATarget, UserAdapter, Answer]):
    """빈 id 목록으로 읽는다."""

    @override
    def operation(self) -> str:
        return "batch_load_by_ids"

    @override
    def describe(self, laid: AReaderAndATarget) -> str:
        return f"{laid.caller.username}이 빈 목록으로 일괄 읽음"

    @override
    async def call(self, adapter: UserAdapter, laid: AReaderAndATarget) -> Answer:
        with ActingAs(laid.caller):
            return await adapter.batch_load_by_ids([])


@dataclass(frozen=True)
class TheTargetNode(Then[AReaderAndATarget, Answer]):
    """읽힌 사용자 노드가 통째로 온다."""

    started: datetime

    @override
    def says(self) -> str:
        return "읽힌 사용자 전체가 온다"

    @override
    def look(self, laid: AReaderAndATarget, answered: Answered[Answer]) -> list[Verdict]:
        node = answered.response
        if not isinstance(node, UserNode):
            return [Refused(NotEnoughPermission, answered.raised)]
        return UserNodeLook(self.started).verdicts(node, laid.target)


@dataclass(frozen=True)
class EachElementInOrder(Then[AReaderAndTwoUsers, Answer]):
    """원소마다 노드와 거부가 입력 순서대로 온다."""

    started: datetime

    @override
    def says(self) -> str:
        return "원소마다 결과가 입력 순서대로 온다"

    @override
    def look(self, laid: AReaderAndTwoUsers, answered: Answered[Answer]) -> list[Verdict]:
        loaded = answered.response
        if not isinstance(loaded, list):
            return [Refused(NotEnoughPermission, answered.raised)]
        first, second, third = loaded
        seen: list[Verdict] = [Same("length", len(loaded), 3)]
        if isinstance(first, UserNode):
            seen.extend(UserNodeLook(self.started).verdicts(first, laid.readable, at="[0]."))
        else:
            seen.append(Same("[0]", type(first).__name__, "UserNode"))
        seen.append(Refused(NotEnoughPermission, second if isinstance(second, Exception) else None))
        seen.append(Refused(NotEnoughPermission, third if isinstance(third, Exception) else None))
        return seen


@dataclass(frozen=True)
class TheNodeThenNothing(Then[AReaderAndATarget, Answer]):
    """있는 사람은 노드, 없는 id는 빈 값."""

    started: datetime

    @override
    def says(self) -> str:
        return "있는 사람은 노드, 없는 id 자리는 비어서 온다"

    @override
    def look(self, laid: AReaderAndATarget, answered: Answered[Answer]) -> list[Verdict]:
        loaded = answered.response
        if not isinstance(loaded, list):
            return [Refused(NotEnoughPermission, answered.raised)]
        first, second = loaded
        seen: list[Verdict] = [Same("length", len(loaded), 2)]
        if isinstance(first, UserNode):
            seen.extend(UserNodeLook(self.started).verdicts(first, laid.target, at="[0]."))
        else:
            seen.append(Same("[0]", type(first).__name__, "UserNode"))
        seen.append(Same("[1]", second, None))
        return seen


@dataclass(frozen=True)
class AnEmptyList(Then[AReaderAndATarget, Answer]):
    """빈 목록이 온다."""

    @override
    def says(self) -> str:
        return "빈 목록이 온다"

    @override
    def look(self, laid: AReaderAndATarget, answered: Answered[Answer]) -> list[Verdict]:
        if answered.raised is not None:
            return [Same("raised", type(answered.raised).__name__, None)]
        return [Same("loaded", answered.response, [])]


@dataclass(frozen=True)
class AGrantedUserReadsAnother(Scenario[SeedingSession, AReaderAndATarget, UserAdapter, Answer]):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-read-on-another-user-reads-their-whole-node"

    @override
    def describe(self) -> str:
        return (
            "대상 사용자 스코프에서 사용자 읽기 권한을 받은 사용자가 읽으면, "
            "기본 키까지 채운 노드 전체가 답으로 온다"
        )

    @override
    def given(self) -> Given[SeedingSession, AReaderAndATarget]:
        return SomeoneAndAnother(granted=True)

    @override
    def when(self) -> When[AReaderAndATarget, UserAdapter, Answer]:
        return ReadingTheTarget()

    @override
    def then(self) -> Then[AReaderAndATarget, Answer]:
        return TheTargetNode(started=self.started)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotReadAnother(
    Scenario[SeedingSession, AReaderAndATarget, UserAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-read-another-user"

    @override
    def describe(self) -> str:
        return "아무 역할도 받지 않은 사용자가 다른 사용자를 읽으려 하면, 엔티티 권한 문이 막는다"

    @override
    def given(self) -> Given[SeedingSession, AReaderAndATarget]:
        return SomeoneAndAnother(granted=False)

    @override
    def when(self) -> When[AReaderAndATarget, UserAdapter, Answer]:
        return ReadingTheTarget()

    @override
    def then(self) -> Then[AReaderAndATarget, Answer]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class ABatchLoadAnswersEachElementInOrder(
    Scenario[SeedingSession, AReaderAndTwoUsers, UserAdapter, Answer]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-batch-load-answers-a-node-or-a-refusal-for-each-id-in-order"

    @override
    def describe(self) -> str:
        return (
            "한 사용자에게만 읽기 권한을 받은 사용자가 읽을 수 있는 사용자, 읽을 수 없는 사용자, "
            "없는 id를 한 번에 요청하면, 입력 순서대로 원소별 결과가 온다"
        )

    @override
    def given(self) -> Given[SeedingSession, AReaderAndTwoUsers]:
        return SomeoneReadingOneOfTwo()

    @override
    def when(self) -> When[AReaderAndTwoUsers, UserAdapter, Answer]:
        return LoadingReadableUnreadableAndMissing()

    @override
    def then(self) -> Then[AReaderAndTwoUsers, Answer]:
        return EachElementInOrder(started=self.started)


@dataclass(frozen=True)
class TheSuperadminBatchLoadLeavesAMissingIdEmpty(
    Scenario[SeedingSession, AReaderAndATarget, UserAdapter, Answer]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-batch-load-leaves-a-missing-id-empty"

    @override
    def describe(self) -> str:
        return (
            "슈퍼관리자가 있는 id와 없는 id를 함께 요청하면, "
            "권한 문을 지나 없는 원소 자리에 빈 값이 온다"
        )

    @override
    def given(self) -> Given[SeedingSession, AReaderAndATarget]:
        return SomeoneAndAnother(granted=False, role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AReaderAndATarget, UserAdapter, Answer]:
        return LoadingTheTargetAndMissing()

    @override
    def then(self) -> Then[AReaderAndATarget, Answer]:
        return TheNodeThenNothing(started=self.started)


@dataclass(frozen=True)
class ABatchLoadOfNothingAnswersNothing(
    Scenario[SeedingSession, AReaderAndATarget, UserAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-batch-load-of-no-ids-answers-an-empty-list"

    @override
    def describe(self) -> str:
        return "권한 없는 사용자가 빈 id 목록을 주면, 어떤 액션도 부르지 않고 빈 목록이 답으로 온다"

    @override
    def given(self) -> Given[SeedingSession, AReaderAndATarget]:
        return SomeoneAndAnother(granted=False)

    @override
    def when(self) -> When[AReaderAndATarget, UserAdapter, Answer]:
        return LoadingNothing()

    @override
    def then(self) -> Then[AReaderAndATarget, Answer]:
        return AnEmptyList()


SCENARIOS: list[Scenario[SeedingSession, Any, UserAdapter, Answer]] = [
    AGrantedUserReadsAnother(started=datetime.now(UTC)),
    AUserGrantedNothingMayNotReadAnother(),
    ABatchLoadAnswersEachElementInOrder(started=datetime.now(UTC)),
    TheSuperadminBatchLoadLeavesAMissingIdEmpty(started=datetime.now(UTC)),
    ABatchLoadOfNothingAnswersNothing(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_reading(
    scenario: Scenario[SeedingSession, Any, UserAdapter, Answer],
    adapter: UserAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
