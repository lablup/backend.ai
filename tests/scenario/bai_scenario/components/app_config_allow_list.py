"""app_config_allow_list 어댑터의 시나리오 구성 요소."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, override
from uuid import UUID

from ai.backend.common.data.app_config.types import AppConfigScopeType
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.app_config_allow_list.response import (
    AppConfigAllowListNode,
    SearchAppConfigAllowListPayload,
)
from ai.backend.manager.data.app_config.types import AppConfigAllowListData
from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    Refused,
    Same,
    SameAs,
    Skipped,
    Then,
    Verdict,
)
from bai_scenario.components.answers import MissingResponse
from bai_scenario.components.app_config import UNREGISTERED
from bai_scenario.components.domain import WAS_HERE, SomeoneOf, WrittenByThisRun
from bai_scenario.seeds.app_config.allow_list import SCOPE_NAMES, SeedAllowListEntry
from bai_scenario.seeds.app_config.definition import SeedDefinition
from bai_scenario.seeds.app_config.fragment import SeedPublicFragment
from bai_scenario.seeds.domain.domain import SeedDomain


def _who(role: UserRole) -> str:
    return "슈퍼관리자 한 명" if role == UserRole.SUPERADMIN else "권한이 없는 일반 사용자 한 명"


def in_page_order(
    entries: tuple[AppConfigAllowListData, ...],
) -> tuple[AppConfigAllowListData, ...]:
    """검색이 페이지를 끊는 순서. 생성 시각 내림차순이고, 같으면 ID 오름차순이다.

    한 전제에 심긴 행은 생성 시각이 모두 같으므로 ID가 순서를 정한다.
    """
    ordered = sorted(entries, key=lambda one: one.id)
    ordered.sort(key=lambda one: one.created_at, reverse=True)
    return tuple(ordered)


@dataclass(frozen=True)
class AnEntryAndACaller:
    """설정 이름, 선택적인 allow_list, 호출자."""

    domain: DomainData
    caller: UserData
    name: str
    entry: AppConfigAllowListData | None


@dataclass(frozen=True)
class AnEntryAndSomeone(Given[Any, AnEntryAndACaller]):
    """설정 정의와 allow_list를 만들고 호출자를 준비한다.

    ``opened``가 없으면 정의만 만들고, ``defined``가 거짓이면 정의도 만들지 않는다.
    ``with_fragment``가 참이면 PUBLIC allow_list 아래에 설정 조각도 만든다.
    """

    opened: AppConfigScopeType | None = AppConfigScopeType.PUBLIC
    defined: bool = True
    role: UserRole = UserRole.USER
    with_fragment: bool = False

    @override
    def describe(self) -> str:
        who = _who(self.role)
        if not self.defined:
            return f"등록되지 않은 설정 이름과 {who}"
        if self.opened is None:
            return f"allow_list가 없는 설정 정의 하나와 {who}"
        what = f"{SCOPE_NAMES[self.opened]} 스코프 유형의 allow_list 하나"
        if self.with_fragment:
            what = f"설정 조각이 있는 {what}"
        return f"{what}와 {who}"

    @override
    async def lay(self, seeding: Any) -> AnEntryAndACaller:
        home = await seeding.creating(SeedDomain(name_hint="home", description=WAS_HERE))
        caller = await seeding.within(SomeoneOf(home, role=self.role))
        if not self.defined or self.opened is None:
            name = UNREGISTERED
            if self.defined:
                definition = await seeding.creating(SeedDefinition())
                name = seeding.made(definition).config_name
            return AnEntryAndACaller(
                domain=seeding.made(home), caller=seeding.made(caller), name=name, entry=None
            )
        definition = await seeding.creating(SeedDefinition())
        entry = await seeding.creating_from(SeedAllowListEntry(scope_type=self.opened), definition)
        if self.with_fragment:
            await seeding.creating_from(SeedPublicFragment(config={"theme": "light"}), entry)
        return AnEntryAndACaller(
            domain=seeding.made(home),
            caller=seeding.made(caller),
            name=seeding.made(definition).config_name,
            entry=seeding.made(entry),
        )


@dataclass(frozen=True)
class ManyEntriesAndACaller:
    """검색할 allow_list와 호출자."""

    caller: UserData
    laid: tuple[AppConfigAllowListData, ...]


@dataclass(frozen=True)
class EntriesLaidAcross(Given[Any, ManyEntriesAndACaller]):
    """설정 이름마다 지정한 스코프 유형의 allow_list를 만든다."""

    names: int = 1
    kinds: tuple[AppConfigScopeType, ...] = (AppConfigScopeType.PUBLIC,)
    role: UserRole = UserRole.USER

    @override
    def describe(self) -> str:
        kinds = "·".join(SCOPE_NAMES[one] for one in self.kinds)
        return (
            f"설정 이름 {self.names}개에 각각 {kinds} 스코프 유형의 allow_list와 {_who(self.role)}"
        )

    @override
    async def lay(self, seeding: Any) -> ManyEntriesAndACaller:
        home = await seeding.creating(SeedDomain(name_hint="home", description=WAS_HERE))
        laid = []
        for _ in range(self.names):
            definition = await seeding.creating(SeedDefinition(name_hint="definition"))
            for kind in self.kinds:
                laid.append(
                    await seeding.creating_from(SeedAllowListEntry(scope_type=kind), definition)
                )
        caller = await seeding.within(SomeoneOf(home, role=self.role))
        return ManyEntriesAndACaller(
            caller=seeding.made(caller),
            laid=tuple(seeding.made(one) for one in laid),
        )


@dataclass(frozen=True)
class TwoEntriesAndACaller:
    """ID로 함께 조회할 allow_list 둘과 호출자."""

    caller: UserData
    first: AppConfigAllowListData
    second: AppConfigAllowListData


@dataclass(frozen=True)
class TwoEntriesAndSomeone(Given[Any, TwoEntriesAndACaller]):
    """한 설정 이름에 속한 allow_list 둘과 호출자를 준비한다."""

    role: UserRole = UserRole.USER

    @override
    def describe(self) -> str:
        return f"한 설정 이름의 PUBLIC·USER allow_list와 {_who(self.role)}"

    @override
    async def lay(self, seeding: Any) -> TwoEntriesAndACaller:
        home = await seeding.creating(SeedDomain(name_hint="home", description=WAS_HERE))
        definition = await seeding.creating(SeedDefinition())
        first = await seeding.creating_from(
            SeedAllowListEntry(scope_type=AppConfigScopeType.PUBLIC, name_hint="first"), definition
        )
        second = await seeding.creating_from(
            SeedAllowListEntry(scope_type=AppConfigScopeType.USER, name_hint="second"), definition
        )
        caller = await seeding.within(SomeoneOf(home, role=self.role))
        return TwoEntriesAndACaller(
            caller=seeding.made(caller), first=seeding.made(first), second=seeding.made(second)
        )


@dataclass(frozen=True)
class TheEntryNode(Then[AnEntryAndACaller, AppConfigAllowListNode]):
    """준비한 allow_list의 모든 필드가 반환된다."""

    started: datetime
    rank: int | None = None

    @override
    def says(self) -> str:
        return "준비한 allow_list의 모든 필드가 반환된다"

    @override
    def look(
        self, laid: AnEntryAndACaller, answered: Answered[AppConfigAllowListNode]
    ) -> list[Verdict]:
        node = answered.response
        if node is None or laid.entry is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        written = WrittenByThisRun(self.started)
        return [
            Held("id", node.id, SameAs[UUID](laid.entry.id, "준비한 ID")),
            Same("config_name", node.config_name, laid.entry.config_name),
            Same("scope_type", node.scope_type, laid.entry.scope_type),
            Same("rank", node.rank, self.rank if self.rank is not None else laid.entry.rank),
            Held("created_at", node.created_at, written),
            Held("updated_at", node.updated_at, written),
        ]


@dataclass(frozen=True)
class TheNewEntryNode(Then[AnEntryAndACaller, AppConfigAllowListNode]):
    """생성한 allow_list의 모든 필드가 반환된다."""

    started: datetime
    scope_type: AppConfigScopeType
    rank: int

    @override
    def says(self) -> str:
        return "생성한 allow_list의 모든 필드가 반환된다"

    @override
    def look(
        self, laid: AnEntryAndACaller, answered: Answered[AppConfigAllowListNode]
    ) -> list[Verdict]:
        node = answered.response
        if node is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        written = WrittenByThisRun(self.started)
        return [
            Skipped("id", "데이터베이스가 만든다"),
            Same("config_name", node.config_name, laid.name),
            Same("scope_type", node.scope_type, self.scope_type),
            Same("rank", node.rank, self.rank),
            Held("created_at", node.created_at, written),
            Held("updated_at", node.updated_at, written),
        ]


@dataclass(frozen=True)
class EveryLaidEntryIsFound(Then[ManyEntriesAndACaller, SearchAppConfigAllowListPayload]):
    """준비한 allow_list만 모두 반환된다."""

    @override
    def says(self) -> str:
        return "준비한 allow_list만 모두 반환된다"

    @override
    def look(
        self, laid: ManyEntriesAndACaller, answered: Answered[SearchAppConfigAllowListPayload]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        return [
            Same(
                "items",
                sorted((one.config_name, one.scope_type) for one in payload.items),
                sorted((one.config_name, one.scope_type) for one in laid.laid),
            ),
            Same("total_count", payload.total_count, len(laid.laid)),
            Same("has_next_page", payload.has_next_page, False),
            Same("has_previous_page", payload.has_previous_page, False),
        ]


@dataclass(frozen=True)
class TheEntryAfterTheCursorIsFound(Then[ManyEntriesAndACaller, SearchAppConfigAllowListPayload]):
    """커서가 가리킨 allow_list 바로 다음 하나만 반환된다."""

    @override
    def says(self) -> str:
        return "커서 다음 allow_list 하나가 오고 앞뒤 페이지가 모두 있다고 응답한다"

    @override
    def look(
        self, laid: ManyEntriesAndACaller, answered: Answered[SearchAppConfigAllowListPayload]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [MissingResponse(answered.raised)]
        ordered = in_page_order(laid.laid)
        return [
            Held[tuple[UUID, ...]](
                "items",
                tuple(one.id for one in payload.items),
                SameAs[tuple[UUID, ...]]((ordered[1].id,), "커서 다음 allow_list 하나"),
            ),
            Same("total_count", payload.total_count, len(laid.laid)),
            Same("has_next_page", payload.has_next_page, True),
            Same("has_previous_page", payload.has_previous_page, True),
        ]
