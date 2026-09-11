"""What an app config fragment scenario table says besides the call.

A fragment is written and read at its owner's scope, so a row names who owns the
fragment it lays and where the caller's role sits. The public fragment owns nothing,
and a row naming it lays no owner.
"""

from __future__ import annotations

import enum
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any, override
from uuid import UUID, uuid4

from bai_scenario.components.app_config import (
    UNREGISTERED,
    ADesignOf,
    SomeoneGrantedOn,
    SomeoneGrantedOnTheirOwn,
    domain_owner,
    names_of,
    user_owner,
)
from bai_scenario.components.domain import WAS_HERE, SomeoneOf, WrittenByThisRun
from bai_scenario.seeds.app_config.allow_list import SCOPE_NAMES
from bai_scenario.seeds.app_config.fragment import SeedFragmentOf, SeedPublicFragment
from bai_scenario.seeds.domain.domain import SeedDomain
from bai_scenario.seeds.seeder import Laid

from ai.backend.common.data.app_config.types import AppConfigScopeType
from ai.backend.common.data.entity.app_config_fragment import AppConfigFragmentEntityType
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.app_config_fragment.response import (
    AppConfigFragmentNode,
    SearchAppConfigFragmentPayload,
    UpsertAppConfigFragmentsPayload,
)
from ai.backend.manager.data.app_config.types import AppConfigFragmentData
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

FRAGMENT = AppConfigFragmentEntityType()
WRITING = (Permission.CREATE, Permission.UPDATE)
"""쓰기는 생성일 수도 수정일 수도 있으므로 둘 다 요구한다."""


def _who(granted: Sequence[Permission], role: UserRole, seat: str = "자기 스코프에서") -> str:
    if role == UserRole.SUPERADMIN:
        return "슈퍼관리자 한 명"
    if not granted:
        return "설정 조각 권한이 하나도 없는 사용자 한 명"
    return f"{seat} 설정 조각에 대한 {names_of(granted)} 권한을 받은 사용자 한 명"


class Target(enum.StrEnum):
    """지정한 스코프에 쓰거나 조회하는 시나리오가 어디를 지정하는가."""

    HOME_DOMAIN = "home_domain"
    PUBLIC = "public"
    ANOTHER_USER = "another_user"
    NOBODY = "nobody"

    def kind(self) -> AppConfigScopeType:
        match self:
            case Target.HOME_DOMAIN:
                return AppConfigScopeType.DOMAIN
            case Target.PUBLIC:
                return AppConfigScopeType.PUBLIC
            case Target.ANOTHER_USER | Target.NOBODY:
                return AppConfigScopeType.USER

    def says(self) -> str:
        match self:
            case Target.HOME_DOMAIN:
                return "자기 도메인"
            case Target.PUBLIC:
                return "공개 스코프"
            case Target.ANOTHER_USER:
                return "다른 사용자"
            case Target.NOBODY:
                return "어느 사용자도 아닌 id"


# --- writing ---------------------------------------------------------------------


@dataclass(frozen=True)
class AWritingPlace:
    """자기 조각을 쓸 설정 이름들과, 쓸 사용자. ``existing``은 첫 이름에 이미 있는 자기 조각이다."""

    caller: UserData
    names: tuple[str, ...]
    existing: AppConfigFragmentData | None

    @property
    def scope_type(self) -> AppConfigScopeType:
        return AppConfigScopeType.USER

    @property
    def scope_id(self) -> UUID | None:
        return self.caller.id


@dataclass(frozen=True)
class MyWritingPlace(Given[Any, AWritingPlace]):
    """설정 이름 몇 개와, 자기 스코프에 지정한 쓰기 권한만 받은 사용자 한 명.

    첫 이름은 ``kinds``에 허용되고, ``more_opened``개는 사용자 종류에 추가로 허용되며,
    ``more_unopened``개는 어느 종류에도 허용되지 않는다. ``defined``를 끄면 이름을 등록조차
    하지 않는다.
    """

    kinds: tuple[AppConfigScopeType, ...] = (AppConfigScopeType.USER,)
    more_opened: int = 0
    more_unopened: int = 0
    defined: bool = True
    existing: Mapping[str, Any] | None = None
    granted: tuple[Permission, ...] = ()
    role: UserRole = UserRole.USER

    @override
    def describe(self) -> str:
        who = _who(self.granted, self.role)
        if not self.defined:
            return f"등록되지 않은 설정 이름과, {who}"
        opened = "·".join(SCOPE_NAMES[one] for one in self.kinds)
        what = f"{opened} 스코프에 허용된 설정 이름 하나"
        if self.existing is not None:
            what = f"{what}에 이미 있는 자기 조각"
        if self.more_opened:
            what = f"{what}, 사용자 스코프에 허용된 설정 이름 {self.more_opened}개"
        if self.more_unopened:
            what = f"{what}, 어느 스코프에도 허용되지 않은 설정 이름 {self.more_unopened}개"
        return f"{what}와, {who}"

    @override
    async def lay(self, seeding: Any) -> AWritingPlace:
        home = await seeding.creating(SeedDomain(name_hint="home", description=WAS_HERE))
        caller = await seeding.within(
            SomeoneGrantedOnTheirOwn(home, FRAGMENT, granted=self.granted, role=self.role)
        )
        if not self.defined:
            return AWritingPlace(caller=seeding.made(caller), names=(UNREGISTERED,), existing=None)
        first = await seeding.within(ADesignOf(allowed=self.kinds))
        existing: Laid[AppConfigFragmentData] | None = None
        if self.existing is not None:
            existing = await seeding.creating_from_two(
                SeedFragmentOf(owner_of=user_owner, config=self.existing, name_hint="own-fragment"),
                first.entries[AppConfigScopeType.USER],
                caller,
            )
        names = [seeding.made(first.definition).config_name]
        for _ in range(self.more_opened):
            more = await seeding.within(
                ADesignOf(allowed=(AppConfigScopeType.USER,), name_hint="opened")
            )
            names.append(seeding.made(more.definition).config_name)
        for _ in range(self.more_unopened):
            more = await seeding.within(ADesignOf(allowed=(), name_hint="unopened"))
            names.append(seeding.made(more.definition).config_name)
        return AWritingPlace(
            caller=seeding.made(caller),
            names=tuple(names),
            existing=seeding.made(existing) if existing is not None else None,
        )


@dataclass(frozen=True)
class ATargetAndACaller:
    """지정할 스코프와, 그 안에서 쓰거나 조회할 설정 이름, 그리고 호출할 사용자."""

    caller: UserData
    domain: DomainData
    name: str
    scope_type: AppConfigScopeType
    scope_id: UUID | None
    fragment: AppConfigFragmentData | None

    @property
    def names(self) -> tuple[str, ...]:
        return (self.name,)

    @property
    def existing(self) -> AppConfigFragmentData | None:
        return self.fragment


@dataclass(frozen=True)
class SomewhereToTarget(Given[Any, ATargetAndACaller]):
    """지정할 스코프 하나에 설정 이름을 허용해 두고, 그 스코프에 대해 지정한 권한만 받은 사용자 한 명.

    자기 도메인을 지정하는 시나리오는 역할을 그 도메인에 부여하고, 다른 사용자를 지정하는
    시나리오는 자기 스코프에 부여한다. 공개 스코프 시나리오의 역할은 자기 도메인에 부여되어,
    스코프 권한으로는 전역 역할 검사를 통과하지 못한다는 것을 보인다. ``laid``를 켜면 그
    스코프에 설정 조각을 하나 미리 만들어 둔다.
    """

    target: Target
    laid: Mapping[str, Any] | None = None
    granted: tuple[Permission, ...] = ()
    role: UserRole = UserRole.USER

    @override
    def describe(self) -> str:
        seat = "자기 스코프에서" if self.target == Target.ANOTHER_USER else "자기 도메인에서"
        what = f"{self.target.says()}에 허용된 설정 이름 하나"
        if self.laid is not None:
            what = f"{what}와 거기 있는 설정 조각 하나"
        return f"{what}, 그리고 {_who(self.granted, self.role, seat)}"

    @override
    async def lay(self, seeding: Any) -> ATargetAndACaller:
        home = await seeding.creating(SeedDomain(name_hint="home", description=WAS_HERE))
        design = await seeding.within(ADesignOf(allowed=(self.target.kind(),)))
        entry = design.entries[self.target.kind()]
        if self.target == Target.ANOTHER_USER:
            caller = await seeding.within(
                SomeoneGrantedOnTheirOwn(home, FRAGMENT, granted=self.granted, role=self.role)
            )
        else:
            caller = await seeding.within(
                SomeoneGrantedOn(
                    home, home, domain_owner, FRAGMENT, granted=self.granted, role=self.role
                )
            )
        fragment: Laid[AppConfigFragmentData] | None = None
        scope_id: UUID | None
        match self.target:
            case Target.HOME_DOMAIN:
                scope_id = seeding.made(home).id
                if self.laid is not None:
                    fragment = await seeding.creating_from_two(
                        SeedFragmentOf(owner_of=domain_owner, config=self.laid), entry, home
                    )
            case Target.PUBLIC:
                scope_id = None
                if self.laid is not None:
                    fragment = await seeding.creating_from(
                        SeedPublicFragment(config=self.laid), entry
                    )
            case Target.ANOTHER_USER:
                other = await seeding.within(SomeoneOf(home))
                scope_id = seeding.made(other).id
                if self.laid is not None:
                    fragment = await seeding.creating_from_two(
                        SeedFragmentOf(owner_of=user_owner, config=self.laid), entry, other
                    )
            case Target.NOBODY:
                scope_id = uuid4()
        return ATargetAndACaller(
            caller=seeding.made(caller),
            domain=seeding.made(home),
            name=seeding.made(design.definition).config_name,
            scope_type=self.target.kind(),
            scope_id=scope_id,
            fragment=seeding.made(fragment) if fragment is not None else None,
        )


@dataclass(frozen=True)
class TheWrittenFragments(Then[AWritingPlace | ATargetAndACaller, UpsertAppConfigFragmentsPayload]):
    """쓴 설정 조각이 요청 순서대로 통째로 반환된다.

    값은 시나리오가 정한 것이고, 소유자와 종류는 미리 만들어 둔 스코프에서 읽는다.
    ``replacing``이면 첫 조각의 id가 이미 있던 조각과 같아야 한다.
    """

    started: datetime
    configs: tuple[Mapping[str, Any], ...]
    replacing: bool = False

    @override
    def says(self) -> str:
        return "쓴 설정 조각 전체가 요청 순서대로 반환된다"

    @override
    def look(
        self,
        laid: AWritingPlace | ATargetAndACaller,
        answered: Answered[UpsertAppConfigFragmentsPayload],
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        written = WrittenByThisRun(self.started)
        seen: list[Verdict] = [
            Same("items", len(payload.items), len(self.configs)),
            Same("failed", list(payload.failed), []),
        ]
        for i, (node, config) in enumerate(zip(payload.items, self.configs, strict=False)):
            if self.replacing and i == 0 and laid.existing is not None:
                seen.append(
                    Held(f"items[{i}].id", node.id, SameAs(laid.existing.id, "이미 있던 조각"))
                )
            else:
                seen.append(Skipped(f"items[{i}].id", "데이터베이스가 만든다"))
            seen.extend([
                Held(
                    f"items[{i}].config_name",
                    node.config_name,
                    SameAs(laid.names[i], "요청한 이름"),
                ),
                Same(f"items[{i}].scope_type", node.scope_type, laid.scope_type),
                Held(
                    f"items[{i}].scope_id",
                    node.scope_id,
                    SameAs[UUID | None](
                        laid.scope_id,
                        "지정한 소유자" if laid.scope_id is not None else "소유자 없음",
                    ),
                ),
                Same(f"items[{i}].config", node.config, dict(config)),
                Held(f"items[{i}].created_at", node.created_at, written),
                Held(f"items[{i}].updated_at", node.updated_at, written),
            ])
        return seen


# --- reading by name -----------------------------------------------------------------


@dataclass(frozen=True)
class AReadingPlace:
    """이름으로 조회할 대상. ``mine``은 이름마다 자기 조각이 있으면 그것, 없으면 빈 항목이다."""

    caller: UserData
    names: tuple[str, ...]
    mine: tuple[AppConfigFragmentData | None, ...]


@dataclass(frozen=True)
class MyFragmentsLaid(Given[Any, AReadingPlace]):
    """사용자 스코프에 허용된 설정 이름 몇 개에 자기 조각을 미리 만들어 두고, 그것을 조회할 사용자 한 명.

    ``mine_on``에 든 위치에만 자기 조각이 만들어진다. 첫 이름에는 ``anothers``와 ``domains``로
    다른 사용자와 자기 도메인의 조각을 함께 둘 수 있다. 반환하지 않으므로 섞이면 불일치가
    드러난다.
    """

    names: int = 1
    mine_on: tuple[int, ...] = (0,)
    anothers: Mapping[str, Any] | None = None
    domains: Mapping[str, Any] | None = None
    granted: tuple[Permission, ...] = ()
    role: UserRole = UserRole.USER

    @override
    def describe(self) -> str:
        what = f"사용자 스코프에 허용된 설정 이름 {self.names}개 중 {len(self.mine_on)}개에 있는 자기 조각"
        if self.anothers is not None:
            what = f"{what}, 같은 이름의 다른 사용자 조각"
        if self.domains is not None:
            what = f"{what}, 같은 이름의 자기 도메인 조각"
        return f"{what}과, {_who(self.granted, self.role)}"

    @override
    async def lay(self, seeding: Any) -> AReadingPlace:
        home = await seeding.creating(SeedDomain(name_hint="home", description=WAS_HERE))
        caller = await seeding.within(
            SomeoneGrantedOnTheirOwn(home, FRAGMENT, granted=self.granted, role=self.role)
        )
        names: list[str] = []
        mine: list[AppConfigFragmentData | None] = []
        for i in range(self.names):
            kinds: tuple[AppConfigScopeType, ...] = (AppConfigScopeType.USER,)
            if i == 0 and self.domains is not None:
                kinds = (AppConfigScopeType.USER, AppConfigScopeType.DOMAIN)
            design = await seeding.within(ADesignOf(allowed=kinds))
            names.append(seeding.made(design.definition).config_name)
            if i in self.mine_on:
                own = await seeding.creating_from_two(
                    SeedFragmentOf(
                        owner_of=user_owner, config={"slot": i}, name_hint="own-fragment"
                    ),
                    design.entries[AppConfigScopeType.USER],
                    caller,
                )
                mine.append(seeding.made(own))
            else:
                mine.append(None)
            if i == 0 and self.anothers is not None:
                other = await seeding.within(SomeoneOf(home))
                await seeding.creating_from_two(
                    SeedFragmentOf(
                        owner_of=user_owner, config=self.anothers, name_hint="anothers-fragment"
                    ),
                    design.entries[AppConfigScopeType.USER],
                    other,
                )
            if i == 0 and self.domains is not None:
                await seeding.creating_from_two(
                    SeedFragmentOf(
                        owner_of=domain_owner, config=self.domains, name_hint="domain-fragment"
                    ),
                    design.entries[AppConfigScopeType.DOMAIN],
                    home,
                )
        return AReadingPlace(caller=seeding.made(caller), names=tuple(names), mine=tuple(mine))


@dataclass(frozen=True)
class EachNameAnsweredWithMine(Then[AReadingPlace, list[AppConfigFragmentNode | None]]):
    """이름마다 자기 조각이 있으면 그것, 없으면 빈 항목이 요청 순서대로 반환된다."""

    @override
    def says(self) -> str:
        return "이름마다 자기 조각이 있으면 그 조각, 없으면 빈 항목이 요청 순서대로 반환된다"

    @override
    def look(
        self, laid: AReadingPlace, answered: Answered[list[AppConfigFragmentNode | None]]
    ) -> list[Verdict]:
        items = answered.response
        if items is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        seen: list[Verdict] = [Same("items", len(items), len(laid.names))]
        for i, (got, mine) in enumerate(zip(items, laid.mine, strict=False)):
            if mine is None:
                seen.append(Same(f"items[{i}]", got, None))
            else:
                seen.append(
                    Held[object](
                        f"items[{i}].id",
                        getattr(got, "id", got),
                        SameAs[object](mine.id, "미리 만들어 둔 자기 조각"),
                    )
                )
                seen.append(Same(f"items[{i}].config", getattr(got, "config", got), mine.config))
        return seen


@dataclass(frozen=True)
class TheTargetsFragmentByName(Then[ATargetAndACaller, list[AppConfigFragmentNode | None]]):
    """지정한 스코프에 미리 만들어 둔 설정 조각 하나가 반환된다."""

    @override
    def says(self) -> str:
        return "지정한 스코프의 설정 조각 하나가 반환된다"

    @override
    def look(
        self, laid: ATargetAndACaller, answered: Answered[list[AppConfigFragmentNode | None]]
    ) -> list[Verdict]:
        items = answered.response
        if items is None or laid.fragment is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        seen: list[Verdict] = [Same("items", len(items), 1)]
        if len(items) != 1:
            return seen
        got = items[0]
        return [
            *seen,
            Held[object](
                "items[0].id",
                getattr(got, "id", got),
                SameAs[object](laid.fragment.id, "미리 만들어 둔 조각"),
            ),
            Same("items[0].scope_type", getattr(got, "scope_type", got), laid.scope_type),
            Held[object](
                "items[0].scope_id",
                getattr(got, "scope_id", got),
                SameAs[object](
                    laid.scope_id, "지정한 소유자" if laid.scope_id is not None else "소유자 없음"
                ),
            ),
            Same("items[0].config", getattr(got, "config", got), laid.fragment.config),
        ]


# --- searching -----------------------------------------------------------------------


@dataclass(frozen=True)
class ManyFragmentsAndACaller:
    """검색 대상 설정 조각들과, 검색을 호출할 사용자. ``laid``는 응답에 나와야 하는 것뿐이다."""

    caller: UserData
    domain: DomainData
    laid: tuple[AppConfigFragmentData, ...]
    named: str
    scope_type: AppConfigScopeType
    scope_id: UUID | None
    other_id: UUID | None


@dataclass(frozen=True)
class FragmentsLaidAcross(Given[Any, ManyFragmentsAndACaller]):
    """스코프 종류마다 설정 조각을 미리 만들어 두고, 그중 한 스코프를 검색할 사용자 한 명.

    ``mine``개는 자기 조각, ``publics``개는 공개 조각, ``domains``개는 자기 도메인 조각이고
    ``anothers``는 같은 도메인의 다른 사용자 조각 수다. 설정 이름은 조각마다 하나씩 허용한다.
    ``answers``가 어느 스코프의 것이 응답에 나와야 하는지 정하고, 지정하는 스코프도 그것이다.
    """

    mine: int = 0
    publics: int = 0
    domains: int = 0
    anothers: int = 0
    answers: AppConfigScopeType | None = AppConfigScopeType.USER
    granted: tuple[Permission, ...] = ()
    role: UserRole = UserRole.USER
    missing_domain: bool = False

    @override
    def describe(self) -> str:
        parts = []
        if self.mine:
            parts.append(f"자기 조각 {self.mine}개")
        if self.anothers:
            parts.append(f"다른 사용자의 조각 {self.anothers}개")
        if self.domains:
            parts.append(f"자기 도메인의 조각 {self.domains}개")
        if self.publics:
            parts.append(f"공개 조각 {self.publics}개")
        seat = "자기 도메인에서" if self.answers == AppConfigScopeType.DOMAIN else "자기 스코프에서"
        return f"{', '.join(parts) or '설정 조각 없음'}과, {_who(self.granted, self.role, seat)}"

    @override
    async def lay(self, seeding: Any) -> ManyFragmentsAndACaller:
        home = await seeding.creating(SeedDomain(name_hint="home", description=WAS_HERE))
        if self.answers == AppConfigScopeType.DOMAIN:
            caller = await seeding.within(
                SomeoneGrantedOn(
                    home, home, domain_owner, FRAGMENT, granted=self.granted, role=self.role
                )
            )
        else:
            caller = await seeding.within(
                SomeoneGrantedOnTheirOwn(home, FRAGMENT, granted=self.granted, role=self.role)
            )
        other = await seeding.within(SomeoneOf(home)) if self.anothers else None
        answering: list[Laid[AppConfigFragmentData]] = []
        named = ""
        for i in range(self.mine):
            design = await seeding.within(
                ADesignOf(allowed=(AppConfigScopeType.USER,), name_hint="mine")
            )
            if i == 0:
                named = seeding.made(design.definition).config_name
            own = await seeding.creating_from_two(
                SeedFragmentOf(owner_of=user_owner, config={"mine": i}, name_hint="own-fragment"),
                design.entries[AppConfigScopeType.USER],
                caller,
            )
            if self.answers == AppConfigScopeType.USER:
                answering.append(own)
        for i in range(self.anothers):
            design = await seeding.within(
                ADesignOf(allowed=(AppConfigScopeType.USER,), name_hint="theirs")
            )
            await seeding.creating_from_two(
                SeedFragmentOf(
                    owner_of=user_owner, config={"theirs": i}, name_hint="anothers-fragment"
                ),
                design.entries[AppConfigScopeType.USER],
                other,
            )
        for i in range(self.domains):
            design = await seeding.within(
                ADesignOf(allowed=(AppConfigScopeType.DOMAIN,), name_hint="domains")
            )
            if not named:
                named = seeding.made(design.definition).config_name
            laid = await seeding.creating_from_two(
                SeedFragmentOf(
                    owner_of=domain_owner, config={"domains": i}, name_hint="domain-fragment"
                ),
                design.entries[AppConfigScopeType.DOMAIN],
                home,
            )
            if self.answers == AppConfigScopeType.DOMAIN:
                answering.append(laid)
        for i in range(self.publics):
            design = await seeding.within(
                ADesignOf(allowed=(AppConfigScopeType.PUBLIC,), name_hint="publics")
            )
            if not named:
                named = seeding.made(design.definition).config_name
            laid = await seeding.creating_from(
                SeedPublicFragment(config={"publics": i}), design.entries[AppConfigScopeType.PUBLIC]
            )
            if self.answers == AppConfigScopeType.PUBLIC:
                answering.append(laid)
        scope_id: UUID | None
        match self.answers:
            case AppConfigScopeType.USER:
                scope_id = seeding.made(caller).id
            case AppConfigScopeType.DOMAIN:
                scope_id = uuid4() if self.missing_domain else seeding.made(home).id
            case _:
                scope_id = None
        return ManyFragmentsAndACaller(
            caller=seeding.made(caller),
            domain=seeding.made(home),
            laid=tuple(seeding.made(one) for one in answering),
            named=named,
            scope_type=self.answers or AppConfigScopeType.PUBLIC,
            scope_id=scope_id,
            other_id=seeding.made(other).id if other is not None else None,
        )


@dataclass(frozen=True)
class EveryAnsweringFragmentIsFound(Then[ManyFragmentsAndACaller, SearchAppConfigFragmentPayload]):
    """응답에 나와야 하는 설정 조각이 모두, 그리고 그것만 집계된다."""

    @override
    def says(self) -> str:
        return "그 스코프의 설정 조각이 모두, 그리고 그것만 집계된다"

    @override
    def look(
        self, laid: ManyFragmentsAndACaller, answered: Answered[SearchAppConfigFragmentPayload]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        return [
            Same(
                "items",
                sorted(one.config_name for one in payload.items),
                sorted(one.config_name for one in laid.laid),
            ),
            Same("total_count", payload.total_count, len(laid.laid)),
            Same("has_next_page", payload.has_next_page, False),
            Same("has_previous_page", payload.has_previous_page, False),
        ]


@dataclass(frozen=True)
class OnlyTheNamedFragmentIsFound(Then[ManyFragmentsAndACaller, SearchAppConfigFragmentPayload]):
    """필터에 맞는 이름의 조각만 반환된다."""

    @override
    def says(self) -> str:
        return "이름 필터에 맞는 설정 조각만 반환된다"

    @override
    def look(
        self, laid: ManyFragmentsAndACaller, answered: Answered[SearchAppConfigFragmentPayload]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        return [
            Same("items", [one.config_name for one in payload.items], [laid.named]),
            Same("total_count", payload.total_count, 1),
            Same("has_next_page", payload.has_next_page, False),
            Same("has_previous_page", payload.has_previous_page, False),
        ]


@dataclass(frozen=True)
class OnlyOneKindsFragmentsAreFound(Then[ManyFragmentsAndACaller, SearchAppConfigFragmentPayload]):
    """필터에 맞는 종류의 조각만 반환된다."""

    kind: AppConfigScopeType
    count: int

    @override
    def says(self) -> str:
        return f"{SCOPE_NAMES[self.kind]} 종류의 설정 조각만 반환된다"

    @override
    def look(
        self, laid: ManyFragmentsAndACaller, answered: Answered[SearchAppConfigFragmentPayload]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        return [
            Same("items", [one.scope_type for one in payload.items], [self.kind] * self.count),
            Same("total_count", payload.total_count, self.count),
        ]


@dataclass(frozen=True)
class TenFragmentsComeWithANextPage(Then[ManyFragmentsAndACaller, SearchAppConfigFragmentPayload]):
    """크기를 지정하지 않으면 10건까지 반환되고 다음 페이지가 있다고 응답한다."""

    @override
    def says(self) -> str:
        return "10건까지 반환되고 다음 페이지가 있다고 응답한다"

    @override
    def look(
        self, laid: ManyFragmentsAndACaller, answered: Answered[SearchAppConfigFragmentPayload]
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


# --- one fragment by id ----------------------------------------------------------


class Whose(enum.StrEnum):
    """id로 다루는 설정 조각이 누구의 것인가."""

    MINE = "mine"
    ANOTHERS = "anothers"
    PUBLIC = "public"

    def says(self) -> str:
        match self:
            case Whose.MINE:
                return "자기 조각"
            case Whose.ANOTHERS:
                return "다른 사용자의 조각"
            case Whose.PUBLIC:
                return "공개 조각"


@dataclass(frozen=True)
class AFragmentAndACaller:
    """설정 조각 하나와, 그것을 호출할 사용자."""

    caller: UserData
    fragment: AppConfigFragmentData
    owner: EntityIdentifier | None


@dataclass(frozen=True)
class AFragmentAndSomeone(Given[Any, AFragmentAndACaller]):
    """설정 조각 하나와, 자기 스코프에 지정한 권한만 받은 사용자 한 명."""

    whose: Whose = Whose.MINE
    granted: tuple[Permission, ...] = ()
    role: UserRole = UserRole.USER

    @override
    def describe(self) -> str:
        return f"{self.whose.says()} 하나와, {_who(self.granted, self.role)}"

    @override
    async def lay(self, seeding: Any) -> AFragmentAndACaller:
        home = await seeding.creating(SeedDomain(name_hint="home", description=WAS_HERE))
        caller = await seeding.within(
            SomeoneGrantedOnTheirOwn(home, FRAGMENT, granted=self.granted, role=self.role)
        )
        owner: EntityIdentifier | None
        fragment: Laid[AppConfigFragmentData]
        if self.whose == Whose.MINE:
            design = await seeding.within(ADesignOf(allowed=(AppConfigScopeType.USER,)))
            fragment = await seeding.creating_from_two(
                SeedFragmentOf(
                    owner_of=user_owner, config={"theme": "mine"}, name_hint="own-fragment"
                ),
                design.entries[AppConfigScopeType.USER],
                caller,
            )
            owner = user_owner(seeding.made(caller))
        elif self.whose == Whose.ANOTHERS:
            design = await seeding.within(ADesignOf(allowed=(AppConfigScopeType.USER,)))
            other = await seeding.within(SomeoneOf(home))
            fragment = await seeding.creating_from_two(
                SeedFragmentOf(
                    owner_of=user_owner, config={"theme": "theirs"}, name_hint="anothers-fragment"
                ),
                design.entries[AppConfigScopeType.USER],
                other,
            )
            owner = user_owner(seeding.made(other))
        else:
            design = await seeding.within(ADesignOf(allowed=(AppConfigScopeType.PUBLIC,)))
            fragment = await seeding.creating_from(
                SeedPublicFragment(config={"theme": "public"}),
                design.entries[AppConfigScopeType.PUBLIC],
            )
            owner = None
        return AFragmentAndACaller(
            caller=seeding.made(caller), fragment=seeding.made(fragment), owner=owner
        )


@dataclass(frozen=True)
class TheFragmentNode(Then[AFragmentAndACaller, AppConfigFragmentNode]):
    """미리 만들어 둔 설정 조각이 통째로 반환된다."""

    started: datetime

    @override
    def says(self) -> str:
        return "미리 만들어 둔 설정 조각 전체가 반환된다"

    @override
    def look(
        self, laid: AFragmentAndACaller, answered: Answered[AppConfigFragmentNode]
    ) -> list[Verdict]:
        node = answered.response
        if node is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        written = WrittenByThisRun(self.started)
        return [
            Held("id", node.id, SameAs(laid.fragment.id, "미리 만들어 둔 조각")),
            Same("config_name", node.config_name, laid.fragment.config_name),
            Same("scope_type", node.scope_type, AppConfigScopeType.of_owner(laid.owner)),
            Held[object](
                "scope_id",
                node.scope_id,
                SameAs[object](
                    laid.owner,
                    "미리 만들어 둔 조각의 소유자" if laid.owner is not None else "소유자 없음",
                ),
            ),
            Same("config", node.config, laid.fragment.config),
            Held("created_at", node.created_at, written),
            Held("updated_at", node.updated_at, written),
        ]


@dataclass(frozen=True)
class SomeFragmentsAndACaller:
    """id로 함께 다룰 설정 조각들과, 호출할 사용자. 앞의 ``mine``은 자기 것, ``theirs``는 남의 것이다."""

    caller: UserData
    mine: tuple[AppConfigFragmentData, ...]
    theirs: AppConfigFragmentData


@dataclass(frozen=True)
class SomeFragmentsAndSomeone(Given[Any, SomeFragmentsAndACaller]):
    """자기 조각 몇 개와 다른 사용자의 조각 하나, 그리고 자기 스코프에 지정한 권한만 받은 사용자."""

    mine: int = 1
    granted: tuple[Permission, ...] = ()
    role: UserRole = UserRole.USER

    @override
    def describe(self) -> str:
        return f"자기 조각 {self.mine}개와 다른 사용자의 조각 하나, 그리고 {_who(self.granted, self.role)}"

    @override
    async def lay(self, seeding: Any) -> SomeFragmentsAndACaller:
        home = await seeding.creating(SeedDomain(name_hint="home", description=WAS_HERE))
        caller = await seeding.within(
            SomeoneGrantedOnTheirOwn(home, FRAGMENT, granted=self.granted, role=self.role)
        )
        other = await seeding.within(SomeoneOf(home))
        mine = []
        for i in range(self.mine):
            design = await seeding.within(
                ADesignOf(allowed=(AppConfigScopeType.USER,), name_hint="mine")
            )
            mine.append(
                await seeding.creating_from_two(
                    SeedFragmentOf(
                        owner_of=user_owner, config={"mine": i}, name_hint="own-fragment"
                    ),
                    design.entries[AppConfigScopeType.USER],
                    caller,
                )
            )
        design = await seeding.within(
            ADesignOf(allowed=(AppConfigScopeType.USER,), name_hint="theirs")
        )
        theirs = await seeding.creating_from_two(
            SeedFragmentOf(
                owner_of=user_owner, config={"theirs": 0}, name_hint="anothers-fragment"
            ),
            design.entries[AppConfigScopeType.USER],
            other,
        )
        return SomeFragmentsAndACaller(
            caller=seeding.made(caller),
            mine=tuple(seeding.made(one) for one in mine),
            theirs=seeding.made(theirs),
        )
