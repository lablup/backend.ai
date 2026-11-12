"""app_config_allow_list 어댑터의 시나리오 구성 요소."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, override
from uuid import UUID

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
    Language,
    Refused,
    Same,
    SameAs,
    Says,
    Skipped,
    Then,
    Verdict,
    in_language,
)
from bai_scenario.components.answers import MissingResponse
from bai_scenario.components.app_config import (
    UNREGISTERED,
    SomeoneGrantedInGlobal,
    names_of,
)
from bai_scenario.components.domain import WAS_HERE, SomeoneOf, WrittenByThisRun
from bai_scenario.seeds.app_config.allow_list import SCOPE_NAMES, TestSeedAllowListEntry
from bai_scenario.seeds.app_config.definition import TestSeedDefinition
from bai_scenario.seeds.app_config.fragment import TestSeedPublicFragment
from bai_scenario.seeds.domain.domain import TestSeedDomain


def _who(role: UserRole) -> Says:
    if role == UserRole.SUPERADMIN:
        return Says("superadmin 한 명", english="one superadmin")
    return Says(
        "권한이 없는 일반 사용자 한 명",
        english="one Regular user with no permission",
    )


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
        who_en = in_language(who, Language.ENGLISH)
        if not self.defined:
            return Says(
                f"등록되지 않은 설정 이름과 {who}",
                english=f"an unregistered config name and {who_en}",
            )
        if self.opened is None:
            return Says(
                f"allow_list 가 없는 설정 정의 하나와 {who}",
                english=f"one config definition without an allow list, and {who_en}",
            )
        scope = SCOPE_NAMES[self.opened]
        scope_en = in_language(scope, Language.ENGLISH)
        if self.with_fragment:
            return Says(
                f"설정 조각이 있는 {scope} 스코프 유형의 allow_list 하나와 {who}",
                english=(
                    f"one allow-list entry of the {scope_en} scope kind holding a config "
                    f"fragment, and {who_en}"
                ),
            )
        return Says(
            f"{scope} 스코프 유형의 allow_list 하나와 {who}",
            english=f"one allow-list entry of the {scope_en} scope kind, and {who_en}",
        )

    @override
    async def lay(self, seeding: Any) -> AnEntryAndACaller:
        home = await seeding.creating(TestSeedDomain(name_hint="home", description=WAS_HERE))
        caller = await seeding.within(SomeoneOf(home, role=self.role))
        if not self.defined or self.opened is None:
            name = UNREGISTERED
            if self.defined:
                definition = await seeding.creating(TestSeedDefinition())
                name = seeding.made(definition).config_name
            return AnEntryAndACaller(
                domain=seeding.made(home), caller=seeding.made(caller), name=name, entry=None
            )
        definition = await seeding.creating(TestSeedDefinition())
        entry = await seeding.creating_from(
            TestSeedAllowListEntry(scope_type=self.opened), definition
        )
        if self.with_fragment:
            await seeding.creating_from(TestSeedPublicFragment(config={"theme": "light"}), entry)
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
        kinds_ko = ", ".join(str(SCOPE_NAMES[one]) for one in self.kinds)
        kinds_en = ", ".join(in_language(SCOPE_NAMES[one], Language.ENGLISH) for one in self.kinds)
        return Says(
            f"설정 이름 {self.names}개에 각각 {kinds_ko} 스코프 유형의 allow_list 와 {_who(self.role)}",
            english=(
                f"{self.names} config names each with an allow-list entry of the {kinds_en} "
                f"scope kind, and {in_language(_who(self.role), Language.ENGLISH)}"
            ),
        )

    @override
    async def lay(self, seeding: Any) -> ManyEntriesAndACaller:
        home = await seeding.creating(TestSeedDomain(name_hint="home", description=WAS_HERE))
        laid = []
        for _ in range(self.names):
            definition = await seeding.creating(TestSeedDefinition(name_hint="definition"))
            for kind in self.kinds:
                laid.append(
                    await seeding.creating_from(TestSeedAllowListEntry(scope_type=kind), definition)
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
    """한 설정 이름에 속한 allow_list 둘과 호출자를 준비한다.

    ``granted``가 있으면 호출자가 global 스코프에서 그 권한을 받는다.
    """

    role: UserRole = UserRole.USER
    granted: tuple[Permission, ...] = ()

    @override
    def describe(self) -> str:
        if self.granted:
            who = Says(
                f"global 스코프에서 허용 목록 항목에 대한 {names_of(self.granted)} 권한을 "
                "받은 일반 사용자 한 명",
                english=(
                    "one regular user granted the "
                    f"{names_of(self.granted)} permission on allow-list entries in the global scope"
                ),
            )
        else:
            who = _who(self.role)
        return Says(
            f"한 설정 이름의 PUBLIC, USER allow_list 와 {who}",
            english=(
                "the PUBLIC and USER allow-list entries of one config name, and "
                f"{in_language(who, Language.ENGLISH)}"
            ),
        )

    @override
    async def lay(self, seeding: Any) -> TwoEntriesAndACaller:
        home = await seeding.creating(TestSeedDomain(name_hint="home", description=WAS_HERE))
        definition = await seeding.creating(TestSeedDefinition())
        first = await seeding.creating_from(
            TestSeedAllowListEntry(scope_type=AppConfigScopeType.PUBLIC, name_hint="first"),
            definition,
        )
        second = await seeding.creating_from(
            TestSeedAllowListEntry(scope_type=AppConfigScopeType.USER, name_hint="second"),
            definition,
        )
        if self.granted:
            caller = await seeding.within(
                SomeoneGrantedInGlobal(home, AppConfigAllowListEntityType(), granted=self.granted)
            )
        else:
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
        return Says(
            "준비한 allow_list 의 모든 필드가 반환됩니다",
            english="every field of the prepared allow-list entry comes back",
        )

    @override
    def look(
        self, laid: AnEntryAndACaller, answered: Answered[AppConfigAllowListNode]
    ) -> list[Verdict]:
        node = answered.response
        if node is None or laid.entry is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        written = WrittenByThisRun(self.started)
        return [
            Held(
                "id",
                node.id,
                SameAs[UUID](
                    laid.entry.id,
                    Says("준비한 ID", english="the prepared id"),
                ),
            ),
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
        return Says(
            "생성한 allow_list 의 모든 필드가 반환됩니다",
            english="every field of the created allow-list entry comes back",
        )

    @override
    def look(
        self, laid: AnEntryAndACaller, answered: Answered[AppConfigAllowListNode]
    ) -> list[Verdict]:
        node = answered.response
        if node is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        written = WrittenByThisRun(self.started)
        return [
            Skipped(
                "id",
                Says("데이터베이스가 생성합니다", english="the database generates it"),
            ),
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
        return Says(
            "준비한 allow_list 만 모두 반환됩니다",
            english="every prepared allow-list entry comes back, and only those",
        )

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
        return Says(
            "커서 다음 allow_list 하나가 오고 앞뒤 페이지가 모두 있다고 응답합니다",
            english=(
                "one allow-list entry after the cursor comes back and the answer says "
                "pages exist on both sides"
            ),
        )

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
                SameAs[tuple[UUID, ...]](
                    (ordered[1].id,),
                    Says(
                        "커서 다음 allow_list 하나",
                        english="the one allow-list entry after the cursor",
                    ),
                ),
            ),
            Same("total_count", payload.total_count, len(laid.laid)),
            Same("has_next_page", payload.has_next_page, True),
            Same("has_previous_page", payload.has_previous_page, True),
        ]
