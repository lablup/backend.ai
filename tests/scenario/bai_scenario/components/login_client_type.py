"""What a login client type scenario table says besides the call.

A login client type is created in no scope. A table needs the caller, and the type or
types the call reads.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, override
from uuid import UUID

from bai_scenario.components.domain import WrittenByThisRun
from bai_scenario.components.system import KEPT, Kept, lay_a_caller, role_named
from bai_scenario.seeds.login_client_type.login_client_type import SeedLoginClientType

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.login_client_type.response import (
    DeleteLoginClientTypePayload,
    LoginClientTypeNode,
    SearchLoginClientTypesPayload,
)
from ai.backend.manager.data.login_client_type.types import LoginClientTypeData
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.errors.base.entity import EntityNotFoundError
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

DESCRIBED = "미리 만들어 둔 로그인 클라이언트 종류"
"""시드가 미리 만들어 두는 종류의 설명. 시나리오가 기대값으로 다시 쓰므로 한 곳에 둔다."""


@dataclass(frozen=True)
class ATypeAndACaller:
    """종류 하나와, 그것을 호출할 사용자."""

    client_type: LoginClientTypeData
    caller: UserData


@dataclass(frozen=True)
class ManyTypesAndACaller:
    """검색 대상 종류 여럿과, 검색을 호출할 사용자. ``named``는 그중 이름 필터로 골라낼 하나다."""

    laid: tuple[LoginClientTypeData, ...]
    named: LoginClientTypeData
    caller: UserData


@dataclass(frozen=True)
class ATypeAndSomeone(Given[Any, ATypeAndACaller]):
    """종류 하나와 사용자 한 명."""

    role: UserRole = UserRole.USER

    @override
    def describe(self) -> str:
        return f"로그인 클라이언트 종류 하나와, {role_named(self.role)} 한 명"

    @override
    async def lay(self, seeding: Any) -> ATypeAndACaller:
        client_type = await seeding.creating(SeedLoginClientType(description=DESCRIBED))
        caller = await lay_a_caller(seeding, self.role)
        return ATypeAndACaller(seeding.made(client_type), seeding.made(caller))


@dataclass(frozen=True)
class ManyTypesAndSomeone(Given[Any, ManyTypesAndACaller]):
    """종류 여럿과 사용자 한 명."""

    role: UserRole = UserRole.USER
    besides: int = 1

    @override
    def describe(self) -> str:
        return f"로그인 클라이언트 종류 {self.besides + 1}개와, {role_named(self.role)} 한 명"

    @override
    async def lay(self, seeding: Any) -> ManyTypesAndACaller:
        wanted = await seeding.creating(SeedLoginClientType(name_hint="wanted"))
        others = [
            await seeding.creating(SeedLoginClientType(name_hint="other"))
            for _ in range(self.besides)
        ]
        caller = await lay_a_caller(seeding, self.role)
        return ManyTypesAndACaller(
            laid=tuple(seeding.made(one) for one in [wanted, *others]),
            named=seeding.made(wanted),
            caller=seeding.made(caller),
        )


def type_verdicts(
    node: LoginClientTypeNode,
    *,
    named: str,
    described: str | None,
    written: WrittenByThisRun,
) -> list[Verdict]:
    """Every place of one login client type node."""
    return [
        Skipped("id", "데이터베이스가 만든다"),
        Same("name", node.name, named),
        Same("description", node.description, described),
        Held("created_at", node.created_at, written),
        Held("modified_at", node.modified_at, written),
    ]


@dataclass(frozen=True)
class TheNewTypeNode(Then[Any, LoginClientTypeNode]):
    """방금 생성한 종류가 통째로 반환된다. 이름과 설명은 시나리오가 정한 값이다."""

    started: datetime
    named: str
    described: str | None

    @override
    def says(self) -> str:
        return "생성한 종류 전체가 반환된다"

    @override
    def look(self, laid: Any, answered: Answered[LoginClientTypeNode]) -> list[Verdict]:
        node = answered.response
        if node is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        return type_verdicts(
            node,
            named=self.named,
            described=self.described,
            written=WrittenByThisRun(self.started),
        )


@dataclass(frozen=True)
class TheTypeNode(Then[ATypeAndACaller, LoginClientTypeNode]):
    """미리 만들어 둔 종류가 통째로 반환된다. 수정 요청은 바뀌어야 하는 필드만 인자로 준다."""

    started: datetime
    named: str | Kept = KEPT
    described: str | None | Kept = KEPT

    @override
    def says(self) -> str:
        return "미리 만들어 둔 종류 전체가 반환된다"

    @override
    def look(self, laid: ATypeAndACaller, answered: Answered[LoginClientTypeNode]) -> list[Verdict]:
        node = answered.response
        if node is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        seed = laid.client_type
        return type_verdicts(
            node,
            named=seed.name if isinstance(self.named, Kept) else self.named,
            described=seed.description if isinstance(self.described, Kept) else self.described,
            written=WrittenByThisRun(self.started),
        )


@dataclass(frozen=True)
class EveryLaidTypeIsCounted(Then[ManyTypesAndACaller, SearchLoginClientTypesPayload]):
    """미리 만들어 둔 종류가 모두 집계된다."""

    @override
    def says(self) -> str:
        return "미리 만들어 둔 종류가 모두 집계된다"

    @override
    def look(
        self, laid: ManyTypesAndACaller, answered: Answered[SearchLoginClientTypesPayload]
    ) -> list[Verdict]:
        page = answered.response
        if page is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        return [
            Same(
                "items",
                sorted(one.name for one in page.items),
                sorted(one.name for one in laid.laid),
            ),
            Same("total_count", page.total_count, len(laid.laid)),
            Same("has_next_page", page.has_next_page, False),
            Same("has_previous_page", page.has_previous_page, False),
        ]


@dataclass(frozen=True)
class OnlyTheNamedTypeIsLeft(Then[ManyTypesAndACaller, SearchLoginClientTypesPayload]):
    """필터에 맞는 그 하나만 반환된다."""

    @override
    def says(self) -> str:
        return "필터에 맞는 종류 하나만 반환된다"

    @override
    def look(
        self, laid: ManyTypesAndACaller, answered: Answered[SearchLoginClientTypesPayload]
    ) -> list[Verdict]:
        page = answered.response
        if page is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        return [
            Same("items", [one.name for one in page.items], [laid.named.name]),
            Same("total_count", page.total_count, 1),
            Same("has_next_page", page.has_next_page, False),
            Same("has_previous_page", page.has_previous_page, False),
        ]


@dataclass(frozen=True)
class TheFirstPageOfTypes(Then[ManyTypesAndACaller, SearchLoginClientTypesPayload]):
    """크기를 지정하지 않은 첫 페이지. 기본 크기만큼 반환되고 다음 페이지가 있다고 응답한다."""

    size: int

    @override
    def says(self) -> str:
        return "기본 크기의 첫 페이지가 반환된다"

    @override
    def look(
        self, laid: ManyTypesAndACaller, answered: Answered[SearchLoginClientTypesPayload]
    ) -> list[Verdict]:
        page = answered.response
        if page is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        return [
            Same("len(items)", len(page.items), self.size),
            Same("total_count", page.total_count, len(laid.laid)),
            Same("has_next_page", page.has_next_page, True),
            Same("has_previous_page", page.has_previous_page, False),
        ]


@dataclass(frozen=True)
class TheDeletedTypeId(Then[ATypeAndACaller, DeleteLoginClientTypePayload]):
    """삭제한 종류의 id를 담은 응답."""

    @override
    def says(self) -> str:
        return "삭제한 종류의 id가 반환된다"

    @override
    def look(
        self, laid: ATypeAndACaller, answered: Answered[DeleteLoginClientTypePayload]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        return [
            Held[UUID]("id", payload.id, SameAs[UUID](laid.client_type.id, "미리 만들어 둔 종류"))
        ]
