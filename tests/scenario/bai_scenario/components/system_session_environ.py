"""What a system session environ scenario table says besides the call.

A row binds a value source to an environment variable name at the public scope, a
domain or a project. A table needs the caller and the rows the call names.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any, override
from uuid import UUID

from ai.backend.common.data.entity.global_entity import GlobalEntityName
from ai.backend.common.data.entity.system_session_environ import SystemSessionEnvironEntityType
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.system_session_environ.types import (
    SystemSessionEnvironScopeType,
    SystemSessionEnvironValueSource,
)
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.system_session_environ.response import (
    AdminSearchSystemSessionEnvironsPayload,
    ScopedSearchSystemSessionEnvironsPayload,
    SystemSessionEnvironNode,
)
from ai.backend.manager.data.permission.global_entity import global_entity_id
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.data.system_session_environ.types import SystemSessionEnvironData
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
from bai_scenario.components.answers import MissingResponse
from bai_scenario.components.domain import WAS_HERE, SomeoneOf, WrittenByThisRun
from bai_scenario.components.system import ACaller, lay_a_caller, role_named
from bai_scenario.seeds.domain.domain import TestSeedDomain
from bai_scenario.seeds.rbac.role import TestSeedPermission, TestSeedRole
from bai_scenario.seeds.seeder import Laid, TestSeeder, TestSeedNest
from bai_scenario.seeds.system_session_environ.environ import (
    SEEDED_KEY,
    TestSeedDeletedSystemSessionEnviron,
    TestSeedDomainSystemSessionEnviron,
    TestSeedSystemSessionEnviron,
)

OTHER_KEY = "SCENARIO_OTHER_KEY"
"""The key the second seeded row injects under."""

type Loaded = list[SystemSessionEnvironNode | Exception | None]


def _holding(role: UserRole, granted: tuple[Permission, ...]) -> Says:
    if granted:
        names = ", ".join(str(one.name) for one in granted)
        return Says(
            f"public 에서 시스템 세션 환경변수에 {names} 권한을 받은 사용자 한 명",
            english=f"one user granted {names} on system session environs in the public scope",
        )
    who = role_named(role)
    return Says(f"{who} 한 명", english=f"one {in_language(who, Language.ENGLISH)}")


async def lay_a_granted_caller(
    seeding: Any, role: UserRole = UserRole.USER, granted: tuple[Permission, ...] = ()
) -> Laid[UserData]:
    """A user of the given role, granted the given permissions in the public scope."""
    if not granted:
        return await lay_a_caller(seeding, role)
    home = await seeding.creating(TestSeedDomain(name_hint="home", description=WAS_HERE))
    granted_caller: Laid[UserData] = await seeding.within(SomeoneGrantedInPublic(home, granted))
    return granted_caller


@dataclass(frozen=True)
class AnEnvironAndACaller:
    """시스템 세션 환경변수 하나와, 그것을 부를 사용자."""

    environ: SystemSessionEnvironData
    caller: UserData


@dataclass(frozen=True)
class ManyEnvironsAndACaller:
    """시스템 세션 환경변수 여럿과, 그것들을 한 번에 부를 사용자.

    ``outside`` holds the rows seeded at another scope, which a scoped call must not return.
    """

    laid: tuple[SystemSessionEnvironData, ...]
    caller: UserData
    outside: tuple[SystemSessionEnvironData, ...] = ()


@dataclass(frozen=True)
class AnEnvironAndSomeone(Given[Any, AnEnvironAndACaller]):
    """public 범위에 등록된 시스템 세션 환경변수 하나와 사용자 한 명."""

    role: UserRole = UserRole.USER
    granted: tuple[Permission, ...] = ()

    @override
    def describe(self) -> str:
        who = _holding(self.role, self.granted)
        return Says(
            f"public 범위에 등록된 시스템 세션 환경변수 하나와, {who}",
            english=(
                "one system session environ registered at the public scope and "
                f"{in_language(who, Language.ENGLISH)}"
            ),
        )

    @override
    async def lay(self, seeding: Any) -> AnEnvironAndACaller:
        environ = await seeding.creating(TestSeedSystemSessionEnviron())
        caller = await lay_a_granted_caller(seeding, self.role, self.granted)
        return AnEnvironAndACaller(seeding.made(environ), seeding.made(caller))


@dataclass(frozen=True)
class ADeletedEnvironAndSomeone(Given[Any, AnEnvironAndACaller]):
    """public 범위에 등록했다가 지운 시스템 세션 환경변수 하나와 사용자 한 명."""

    role: UserRole = UserRole.USER
    granted: tuple[Permission, ...] = ()

    @override
    def describe(self) -> str:
        who = _holding(self.role, self.granted)
        return Says(
            f"public 범위에서 지운 시스템 세션 환경변수 하나와, {who}",
            english=(
                "one system session environ deleted at the public scope and "
                f"{in_language(who, Language.ENGLISH)}"
            ),
        )

    @override
    async def lay(self, seeding: Any) -> AnEnvironAndACaller:
        environ = await seeding.creating(TestSeedSystemSessionEnviron())
        deleted = await seeding.creating_from(TestSeedDeletedSystemSessionEnviron(), environ)
        caller = await lay_a_granted_caller(seeding, self.role, self.granted)
        return AnEnvironAndACaller(seeding.made(deleted), seeding.made(caller))


@dataclass(frozen=True)
class ManyEnvironsAndSomeone(Given[Any, ManyEnvironsAndACaller]):
    """public 범위에 등록된 시스템 세션 환경변수 둘과 사용자 한 명."""

    role: UserRole = UserRole.USER
    granted: tuple[Permission, ...] = ()

    @override
    def describe(self) -> str:
        who = _holding(self.role, self.granted)
        return Says(
            f"public 범위에 등록된 시스템 세션 환경변수 둘과, {who}",
            english=(
                "two system session environs registered at the public scope and "
                f"{in_language(who, Language.ENGLISH)}"
            ),
        )

    @override
    async def lay(self, seeding: Any) -> ManyEnvironsAndACaller:
        first = await seeding.creating(TestSeedSystemSessionEnviron(key=SEEDED_KEY))
        second = await seeding.creating(TestSeedSystemSessionEnviron(key=OTHER_KEY))
        caller = await lay_a_granted_caller(seeding, self.role, self.granted)
        return ManyEnvironsAndACaller(
            laid=(seeding.made(first), seeding.made(second)),
            caller=seeding.made(caller),
        )


def scope_of(environ: SystemSessionEnvironData) -> SystemSessionEnvironScopeType:
    return SystemSessionEnvironScopeType.of_owner(environ.scope_id)


@dataclass(frozen=True)
class ManyEnvironsAndOneOutsidePublic(Given[Any, ManyEnvironsAndACaller]):
    """public 범위의 시스템 세션 환경변수 둘, 다른 범위의 하나와 사용자 한 명."""

    role: UserRole = UserRole.SUPERADMIN
    outside_key: str = OTHER_KEY

    @override
    def describe(self) -> str:
        who = role_named(self.role)
        return Says(
            f"public 범위의 시스템 세션 환경변수 둘, 도메인 범위의 하나와 {who} 한 명",
            english=(
                "two system session environs at the public scope, one at a domain scope and one "
                f"{in_language(who, Language.ENGLISH)}"
            ),
        )

    @override
    async def lay(self, seeding: Any) -> ManyEnvironsAndACaller:
        first = await seeding.creating(TestSeedSystemSessionEnviron(key=SEEDED_KEY))
        second = await seeding.creating(TestSeedSystemSessionEnviron(key=OTHER_KEY))
        elsewhere = await seeding.creating(
            TestSeedDomain(name_hint="elsewhere", description=WAS_HERE)
        )
        outside = await seeding.creating_from(
            TestSeedDomainSystemSessionEnviron(key=self.outside_key), elsewhere
        )
        caller = await lay_a_caller(seeding, self.role)
        return ManyEnvironsAndACaller(
            laid=(seeding.made(first), seeding.made(second)),
            caller=seeding.made(caller),
            outside=(seeding.made(outside),),
        )


@dataclass(frozen=True)
class PublicEnvironsAndAnOutsideRow(Given[Any, ManyEnvironsAndACaller]):
    """public 범위의 시스템 세션 환경변수 둘, 같은 이름을 쓰는 다른 범위의 하나와, public 에서
    읽기 권한을 받은 사용자 한 명."""

    @override
    def describe(self) -> str:
        return Says(
            "public 범위의 시스템 세션 환경변수 둘, 같은 이름을 쓰는 도메인 범위의 하나와, "
            "public 에서 읽기 권한을 받은 사용자 한 명",
            english=(
                "two system session environs at the public scope, one at a domain scope under the "
                "same key, and one user granted read permission in the public scope"
            ),
        )

    @override
    async def lay(self, seeding: Any) -> ManyEnvironsAndACaller:
        first = await seeding.creating(TestSeedSystemSessionEnviron(key=SEEDED_KEY))
        second = await seeding.creating(TestSeedSystemSessionEnviron(key=OTHER_KEY))
        elsewhere = await seeding.creating(
            TestSeedDomain(name_hint="elsewhere", description=WAS_HERE)
        )
        outside = await seeding.creating_from(
            TestSeedDomainSystemSessionEnviron(key=SEEDED_KEY), elsewhere
        )
        home = await seeding.creating(TestSeedDomain(name_hint="home", description=WAS_HERE))
        caller = await seeding.within(SomeoneGrantedInPublic(home, (Permission.READ,)))
        return ManyEnvironsAndACaller(
            laid=(seeding.made(first), seeding.made(second)),
            caller=seeding.made(caller),
            outside=(seeding.made(outside),),
        )


@dataclass(frozen=True)
class SomeoneGrantedInPublic(TestSeedNest[Laid[UserData]]):
    """그 사용자에게 public 에서 이 환경변수에 대한 권한을 준다."""

    domain: Laid[Any]
    granted: tuple[Permission, ...] = (Permission.CREATE,)

    @override
    def kind(self) -> str:
        names = ", ".join(str(one.name) for one in self.granted)
        return Says(
            f"public 에서 시스템 세션 환경변수에 {names} 권한을 받은 사용자 준비",
            english=(
                f"Prepare a user granted {names} on system session environs in the public scope"
            ),
        )

    @override
    def lay(self, seed: TestSeeder) -> Laid[UserData]:
        someone = seed.within(SomeoneOf(self.domain))
        role = seed.creating_from(
            TestSeedRole(
                lambda _: global_entity_id(GlobalEntityName.PUBLIC),
                name_hint="environ-writer",
            ),
            someone,
        )
        for permission in self.granted:
            seed.adding(
                TestSeedPermission(
                    entity_type=SystemSessionEnvironEntityType(), permission=permission
                ),
                role,
            )
        seed.granting(role, someone, role_id=lambda r: r.id, user_id=lambda u: UserID(u.id))
        return someone


@dataclass(frozen=True)
class ACallerGrantedInPublic(Given[Any, ACaller]):
    """public 에서 이 환경변수에 대한 권한을 받은 사용자 한 명."""

    granted: tuple[Permission, ...] = (Permission.CREATE,)

    @override
    def describe(self) -> str:
        names = ", ".join(str(one.name) for one in self.granted)
        return Says(
            f"public 에서 시스템 세션 환경변수에 {names} 권한을 받은 사용자 한 명",
            english=(f"one user granted {names} on system session environs in the public scope"),
        )

    @override
    async def lay(self, seeding: Any) -> ACaller:
        home = await seeding.creating(TestSeedDomain(name_hint="home", description=WAS_HERE))
        caller = await seeding.within(SomeoneGrantedInPublic(home, self.granted))
        return ACaller(seeding.made(caller))


def environ_verdicts(
    at: str,
    node: SystemSessionEnvironNode,
    environ: SystemSessionEnvironData,
    *,
    written: datetime | None = None,
    deleted: Verdict | None = None,
    key: str | None = None,
) -> list[Verdict]:
    """Every place of one row. ``written`` is the time the call just wrote, if it did."""
    seeded = Says("미리 저장한 행", english="the row seeded in advance")
    return [
        Held[UUID](f"{at}entity_id", node.entity_id, SameAs[UUID](environ.id, seeded)),
        Same(f"{at}key", node.key, environ.key if key is None else key),
        Same(f"{at}value_source", node.value_source, environ.value_source.value),
        Same(f"{at}scope.scope_type", node.scope.scope_type, scope_of(environ)),
        Held[UUID](
            f"{at}scope.scope_id",
            node.scope.scope_id,
            SameAs[UUID](
                environ.scope_id,
                Says("그 행이 묶인 범위의 id", english="the id of the scope it is bound to"),
            ),
        ),
        Held(
            f"{at}created_at",
            node.created_at,
            SameAs(
                environ.created_at,
                Says("미리 저장한 행의 생성 시각", english="the row's creation time"),
            ),
        ),
        Held(
            f"{at}updated_at",
            node.updated_at,
            WrittenByThisRun(written)
            if written is not None
            else SameAs(
                environ.updated_at,
                Says("미리 저장한 행의 수정 시각", english="the row's last change time"),
            ),
        ),
        deleted
        if deleted is not None
        else Same(f"{at}deleted_at", node.deleted_at, environ.deleted_at),
    ]


def matching_rows(
    got: list[SystemSessionEnvironNode], wanted: Sequence[SystemSessionEnvironData]
) -> list[Verdict]:
    return [
        Held(
            "items",
            sorted((one.key, one.entity_id) for one in got),
            SameAs(
                sorted((one.key, one.id) for one in wanted),
                Says("미리 저장한 행", english="the rows seeded in advance"),
            ),
        )
    ]


@dataclass(frozen=True)
class TheEnvironNode(Then[AnEnvironAndACaller, SystemSessionEnvironNode]):
    written: datetime | None = None
    key: str | None = None

    @override
    def says(self) -> str:
        return Says(
            "미리 저장한 행 전체가 반환됩니다",
            english="the whole row seeded in advance comes back",
        )

    @override
    def look(
        self, laid: AnEnvironAndACaller, answered: Answered[SystemSessionEnvironNode]
    ) -> list[Verdict]:
        node = answered.response
        if node is None:
            return [MissingResponse(answered.raised)]
        return environ_verdicts("", node, laid.environ, written=self.written, key=self.key)


@dataclass(frozen=True)
class TheRowIsDeleted(Then[AnEnvironAndACaller, SystemSessionEnvironNode]):
    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "미리 저장한 행 전체가 반환되고, 지운 시각과 수정 시각이 이번 실행의 시각입니다",
            english=(
                "the whole row seeded in advance comes back, with the deletion time and the "
                "last change time written by this run"
            ),
        )

    @override
    def look(
        self, laid: AnEnvironAndACaller, answered: Answered[SystemSessionEnvironNode]
    ) -> list[Verdict]:
        node = answered.response
        if node is None:
            return [MissingResponse(answered.raised)]
        return environ_verdicts(
            "",
            node,
            laid.environ,
            written=self.started,
            deleted=Held("deleted_at", node.deleted_at, WrittenByThisRun(self.started)),
        )


@dataclass(frozen=True)
class TheRowIsRestored(Then[AnEnvironAndACaller, SystemSessionEnvironNode]):
    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "미리 저장한 행 전체가 반환되고, 지운 시각은 비어 있으며 수정 시각은 이번 실행의 "
            "시각입니다",
            english=(
                "the whole row seeded in advance comes back with no deletion time and the "
                "last change time written by this run"
            ),
        )

    @override
    def look(
        self, laid: AnEnvironAndACaller, answered: Answered[SystemSessionEnvironNode]
    ) -> list[Verdict]:
        node = answered.response
        if node is None:
            return [MissingResponse(answered.raised)]
        return environ_verdicts(
            "",
            node,
            laid.environ,
            written=self.started,
            deleted=Same("deleted_at", node.deleted_at, None),
        )


@dataclass(frozen=True)
class TheMatchingEnvironIsListed[
    TPayload: (
        AdminSearchSystemSessionEnvironsPayload,
        ScopedSearchSystemSessionEnvironsPayload,
    )
](Then[ManyEnvironsAndACaller, TPayload]):
    """거른 행 하나만 응답에 있고, 범위 밖 행과 필터가 제외하는 행은 없습니다."""

    wanted: int
    outside_scope: bool = True

    @override
    def says(self) -> str:
        if self.outside_scope:
            return Says(
                "거른 행 하나만 반환되고, 범위 밖 행과 필터가 제외하는 행은 오지 않습니다",
                english=(
                    "only the filtered row comes back, and neither the row outside the scope nor "
                    "the row the filter excludes comes back"
                ),
            )
        return Says(
            "거른 행 하나만 반환되고, 필터가 제외하는 행은 오지 않습니다",
            english=(
                "only the filtered row comes back, and the row the filter excludes does not "
                "come back"
            ),
        )

    @override
    def look(self, laid: ManyEnvironsAndACaller, answered: Answered[TPayload]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [MissingResponse(answered.raised)]
        rows: list[Verdict] = matching_rows(payload.items, (laid.laid[self.wanted],))
        return [
            *rows,
            Same("total_count", payload.total_count, 1),
            Same("has_next_page", payload.has_next_page, False),
            Same("has_previous_page", payload.has_previous_page, False),
        ]


@dataclass(frozen=True)
class TheOrderIsKept(Then[ManyEnvironsAndACaller, Loaded]):
    @override
    def says(self) -> str:
        return Says(
            "미리 저장한 행은 요청한 순서대로 반환됩니다",
            english="the rows seeded in advance come back in the requested order",
        )

    @override
    def look(self, laid: ManyEnvironsAndACaller, answered: Answered[Loaded]) -> list[Verdict]:
        got = answered.response
        if got is None:
            return [MissingResponse(answered.raised)]
        if len(got) != len(laid.laid):
            return [Same("length", len(got), len(laid.laid))]
        verdicts: list[Verdict] = [Same("length", len(got), len(laid.laid))]
        for i, (one, environ) in enumerate(zip(got, laid.laid, strict=True)):
            if not isinstance(one, SystemSessionEnvironNode):
                verdicts.append(
                    Same(f"[{i}]", type(one).__name__, SystemSessionEnvironNode.__name__)
                )
                continue
            verdicts += environ_verdicts(f"[{i}].", one, environ)
        return verdicts


@dataclass(frozen=True)
class EveryIdIsRefused(Then[ManyEnvironsAndACaller, Loaded]):
    @override
    def says(self) -> str:
        return Says(
            "항목마다 권한 부족 거부가 담겨 반환됩니다",
            english="every entry comes back holding a rejection for lack of permission",
        )

    @override
    def look(self, laid: ManyEnvironsAndACaller, answered: Answered[Loaded]) -> list[Verdict]:
        got = answered.response
        if got is None:
            return [MissingResponse(answered.raised)]
        return [
            Same("length", len(got), len(laid.laid)),
            *[
                Refused(NotEnoughPermission, one if isinstance(one, Exception) else None)
                for one in got
            ],
        ]


@dataclass(frozen=True)
class TheValueSourcesAreListed(Then[ACaller, list[str]]):
    @override
    def says(self) -> str:
        return Says(
            "매니저가 제공하는 값 출처가 모두 반환됩니다",
            english="every value source the manager provides comes back",
        )

    @override
    def look(self, laid: ACaller, answered: Answered[list[str]]) -> list[Verdict]:
        items = answered.response
        if items is None:
            return [MissingResponse(answered.raised)]
        return [
            Same(
                "items",
                items,
                [one.value for one in SystemSessionEnvironValueSource],
            )
        ]
