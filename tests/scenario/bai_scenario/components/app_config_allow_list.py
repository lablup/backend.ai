"""What an app config allow-list scenario table says besides the call.

An entry belongs to no scope, so the only seat a role can take to reach one is the entry
itself. The situations here lay that seat when a row asks for a grant.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, override
from uuid import UUID

from bai_scenario.components.app_config import (
    UNREGISTERED,
    SomeoneGrantedOn,
    SomeoneGrantedOnTheirOwn,
    names_of,
)
from bai_scenario.components.domain import WAS_HERE, SomeoneOf, WrittenByThisRun
from bai_scenario.seeds.app_config.allow_list import SCOPE_NAMES, SeedAllowListEntry
from bai_scenario.seeds.app_config.definition import SeedDefinition
from bai_scenario.seeds.app_config.fragment import SeedPublicFragment
from bai_scenario.seeds.domain.domain import SeedDomain

from ai.backend.common.data.app_config.types import AppConfigScopeType
from ai.backend.common.data.entity.app_config_allow_list import AppConfigAllowListEntityType
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.app_config_allow_list.response import (
    AppConfigAllowListNode,
    SearchAppConfigAllowListPayload,
)
from ai.backend.manager.data.app_config.types import AppConfigAllowListData
from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.data.permission.types import Permission
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


@dataclass(frozen=True)
class AnEntryAndACaller:
    """이름 하나와 그 이름의 허용 항목 하나(없을 수도 있다), 그리고 부를 사람."""

    domain: DomainData
    caller: UserData
    name: str
    entry: AppConfigAllowListData | None


@dataclass(frozen=True)
class AnEntryAndSomeone(Given[Any, AnEntryAndACaller]):
    """정의 하나에 허용 항목 하나를 열어 두고, 그 항목 자체에 정해진 권한만 받은 사용자 한 명.

    ``opened``를 비우면 정의만 두고, ``defined``를 끄면 정의조차 두지 않는다. 전역 역할이
    문인 줄은 슈퍼관리자를 댄다. ``with_fragment``는 공개 항목 아래 공개 조각을 딸려 둔다.
    """

    opened: AppConfigScopeType | None = AppConfigScopeType.PUBLIC
    defined: bool = True
    granted: tuple[Permission, ...] = ()
    role: UserRole = UserRole.USER
    with_fragment: bool = False

    @override
    def describe(self) -> str:
        if self.role == UserRole.SUPERADMIN:
            who = "슈퍼관리자 한 명"
        elif self.granted:
            who = f"그 항목에 {names_of(self.granted)} 권한을 받은 사용자 한 명"
        else:
            who = "허용 항목 권한을 하나도 받지 않은 사용자 한 명"
        if not self.defined:
            return f"등록되지 않은 이름과, {who}"
        if self.opened is None:
            return f"허용 항목이 없는 정의 하나와, {who}"
        what = f"{SCOPE_NAMES[self.opened]} 스코프에 연 허용 항목 하나"
        if self.with_fragment:
            what = f"조각이 딸린 {what}"
        return f"{what}와, {who}"

    @override
    async def lay(self, seeding: Any) -> AnEntryAndACaller:
        home = await seeding.creating(SeedDomain(name_hint="home", description=WAS_HERE))
        if not self.defined or self.opened is None:
            caller = await seeding.within(SomeoneOf(home, role=self.role))
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
        caller = await seeding.within(
            SomeoneGrantedOn(
                home,
                entry,
                lambda e: e.id,
                AppConfigAllowListEntityType(),
                granted=self.granted,
                role=self.role,
            )
        )
        return AnEntryAndACaller(
            domain=seeding.made(home),
            caller=seeding.made(caller),
            name=seeding.made(definition).config_name,
            entry=seeding.made(entry),
        )


@dataclass(frozen=True)
class ManyEntriesAndACaller:
    """훑을 허용 항목 여럿과, 훑을 사람. ``named``는 그중 골라낼 이름이다."""

    caller: UserData
    laid: tuple[AppConfigAllowListData, ...]
    named: str


@dataclass(frozen=True)
class EntriesLaidAcross(Given[Any, ManyEntriesAndACaller]):
    """이름 몇 개를 등록하고, 이름마다 대준 스코프 종류에 허용 항목을 연다."""

    names: int = 1
    kinds: tuple[AppConfigScopeType, ...] = (AppConfigScopeType.PUBLIC,)
    granted: tuple[Permission, ...] = ()
    role: UserRole = UserRole.USER

    @override
    def describe(self) -> str:
        if self.role == UserRole.SUPERADMIN:
            who = "슈퍼관리자 한 명"
        elif self.granted:
            who = f"자기 스코프에서 허용 항목에 {names_of(self.granted)} 권한을 받은 사용자 한 명"
        else:
            who = "허용 항목 권한을 하나도 받지 않은 사용자 한 명"
        kinds = "·".join(SCOPE_NAMES[one] for one in self.kinds)
        return f"이름 {self.names}개에 각각 {kinds} 스코프로 연 허용 항목들과, {who}"

    @override
    async def lay(self, seeding: Any) -> ManyEntriesAndACaller:
        home = await seeding.creating(SeedDomain(name_hint="home", description=WAS_HERE))
        laid = []
        named = ""
        for i in range(self.names):
            definition = await seeding.creating(
                SeedDefinition(name_hint="wanted" if i == 0 else "other")
            )
            if i == 0:
                named = seeding.made(definition).config_name
            for kind in self.kinds:
                laid.append(
                    await seeding.creating_from(SeedAllowListEntry(scope_type=kind), definition)
                )
        caller = await seeding.within(
            SomeoneGrantedOnTheirOwn(
                home, AppConfigAllowListEntityType(), granted=self.granted, role=self.role
            )
        )
        return ManyEntriesAndACaller(
            caller=seeding.made(caller),
            laid=tuple(seeding.made(one) for one in laid),
            named=named,
        )


@dataclass(frozen=True)
class TwoEntriesAndACaller:
    """id로 함께 읽을 허용 항목 둘과, 읽을 사람."""

    caller: UserData
    first: AppConfigAllowListData
    second: AppConfigAllowListData


@dataclass(frozen=True)
class TwoEntriesAndSomeone(Given[Any, TwoEntriesAndACaller]):
    """항목 둘과, 첫째에만 읽기 권한을 받았거나 아무 권한도 없거나 슈퍼관리자인 사용자."""

    reads_first: bool = False
    role: UserRole = UserRole.USER

    @override
    def describe(self) -> str:
        if self.role == UserRole.SUPERADMIN:
            who = "슈퍼관리자 한 명"
        elif self.reads_first:
            who = "그중 첫째에만 읽기 권한을 받은 사용자 한 명"
        else:
            who = "허용 항목 권한을 하나도 받지 않은 사용자 한 명"
        return f"한 이름을 두 스코프에 연 허용 항목 둘과, {who}"

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
        caller = await seeding.within(
            SomeoneGrantedOn(
                home,
                first,
                lambda e: e.id,
                AppConfigAllowListEntityType(),
                granted=(Permission.READ,) if self.reads_first else (),
                role=self.role,
            )
        )
        return TwoEntriesAndACaller(
            caller=seeding.made(caller), first=seeding.made(first), second=seeding.made(second)
        )


@dataclass(frozen=True)
class TheEntryNode(Then[AnEntryAndACaller, AppConfigAllowListNode]):
    """심은 항목이 통째로 온다. 바꾸는 요청이 쓸 때는 순위만 인자로 받는다."""

    started: datetime
    rank: int | None = None

    @override
    def says(self) -> str:
        return "심은 허용 항목 전체가 온다"

    @override
    def look(
        self, laid: AnEntryAndACaller, answered: Answered[AppConfigAllowListNode]
    ) -> list[Verdict]:
        node = answered.response
        if node is None or laid.entry is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        written = WrittenByThisRun(self.started)
        return [
            Held("id", node.id, SameAs[UUID](laid.entry.id, "심은 허용 항목")),
            Same("config_name", node.config_name, laid.entry.config_name),
            Same("scope_type", node.scope_type, laid.entry.scope_type),
            Same("rank", node.rank, self.rank if self.rank is not None else laid.entry.rank),
            Held("created_at", node.created_at, written),
            Held("updated_at", node.updated_at, written),
        ]


@dataclass(frozen=True)
class TheNewEntryNode(Then[AnEntryAndACaller, AppConfigAllowListNode]):
    """방금 만든 항목이 통째로 온다. 종류와 순위는 시나리오가 정한 것이다."""

    started: datetime
    scope_type: AppConfigScopeType
    rank: int

    @override
    def says(self) -> str:
        return "만든 허용 항목 전체가 온다"

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
    """심은 항목이 모두, 그리고 그것만 세어진다."""

    @override
    def says(self) -> str:
        return "심은 허용 항목이 모두, 그리고 그것만 세어진다"

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
class OnlyTheNamedNamesEntriesAreFound(
    Then[ManyEntriesAndACaller, SearchAppConfigAllowListPayload]
):
    """골라낸 이름의 항목만 남는다."""

    @override
    def says(self) -> str:
        return "이름으로 고른 항목만 남는다"

    @override
    def look(
        self, laid: ManyEntriesAndACaller, answered: Answered[SearchAppConfigAllowListPayload]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        wanted = sorted(
            (one.config_name, one.scope_type) for one in laid.laid if one.config_name == laid.named
        )
        return [
            Same(
                "items", sorted((one.config_name, one.scope_type) for one in payload.items), wanted
            ),
            Same("total_count", payload.total_count, len(wanted)),
            Same("has_next_page", payload.has_next_page, False),
            Same("has_previous_page", payload.has_previous_page, False),
        ]


@dataclass(frozen=True)
class OnlyOneKindsEntriesAreFound(Then[ManyEntriesAndACaller, SearchAppConfigAllowListPayload]):
    """고른 종류의 항목만 남는다."""

    kind: AppConfigScopeType

    @override
    def says(self) -> str:
        return f"{SCOPE_NAMES[self.kind]} 종류의 항목만 남는다"

    @override
    def look(
        self, laid: ManyEntriesAndACaller, answered: Answered[SearchAppConfigAllowListPayload]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        wanted = sorted(
            (one.config_name, one.scope_type) for one in laid.laid if one.scope_type == self.kind
        )
        return [
            Same(
                "items", sorted((one.config_name, one.scope_type) for one in payload.items), wanted
            ),
            Same("total_count", payload.total_count, len(wanted)),
        ]


@dataclass(frozen=True)
class EntriesComeInRankOrder(Then[ManyEntriesAndACaller, SearchAppConfigAllowListPayload]):
    """순위 오름차순으로 온다."""

    @override
    def says(self) -> str:
        return "순위 순서대로 온다"

    @override
    def look(
        self, laid: ManyEntriesAndACaller, answered: Answered[SearchAppConfigAllowListPayload]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        return [
            Same(
                "items", [one.rank for one in payload.items], sorted(one.rank for one in laid.laid)
            ),
            Same("total_count", payload.total_count, len(laid.laid)),
        ]


@dataclass(frozen=True)
class TenEntriesComeWithANextPage(Then[ManyEntriesAndACaller, SearchAppConfigAllowListPayload]):
    """크기를 대지 않으면 열 건까지 오고 다음 쪽이 있다고 답한다."""

    @override
    def says(self) -> str:
        return "열 건까지 오고 다음 쪽이 있다고 답한다"

    @override
    def look(
        self, laid: ManyEntriesAndACaller, answered: Answered[SearchAppConfigAllowListPayload]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        return [
            Same("items", len(payload.items), 10),
            Same("total_count", payload.total_count, len(laid.laid)),
            Same("has_next_page", payload.has_next_page, True),
            Same("has_previous_page", payload.has_previous_page, False),
        ]
