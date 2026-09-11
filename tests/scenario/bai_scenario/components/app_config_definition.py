"""What an app config definition scenario table says besides the call.

A definition belongs to no scope, so no role reaches one: every door is passed by the
superadmin and refused to anyone else. The situations here only choose who calls.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, override
from uuid import UUID

from bai_scenario.components.domain import WAS_HERE, SomeoneOf, WrittenByThisRun
from bai_scenario.seeds.app_config.allow_list import SeedAllowListEntry
from bai_scenario.seeds.app_config.definition import SeedDefinition
from bai_scenario.seeds.app_config.fragment import SeedPublicFragment
from bai_scenario.seeds.domain.domain import SeedDomain

from ai.backend.common.data.app_config.types import AppConfigScopeType
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.app_config_definition.response import (
    AppConfigDefinitionNode,
    SearchAppConfigDefinitionsPayload,
)
from ai.backend.manager.data.app_config.types import AppConfigDefinitionData
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


def _who(role: UserRole) -> str:
    return (
        "슈퍼관리자 한 명" if role == UserRole.SUPERADMIN else "아무 권한도 받지 않은 사용자 한 명"
    )


@dataclass(frozen=True)
class ADefinitionAndACaller:
    """정의 하나와, 그것을 부를 사람."""

    domain: DomainData
    caller: UserData
    definition: AppConfigDefinitionData


@dataclass(frozen=True)
class ADefinitionAndSomeone(Given[Any, ADefinitionAndACaller]):
    """정의 하나와, 슈퍼관리자 또는 아무 권한도 받지 않은 사용자 한 명.

    ``with_fragment``는 그 이름에 공개 허용 항목과 공개 조각을 딸려 둔다.
    """

    role: UserRole = UserRole.USER
    with_fragment: bool = False

    @override
    def describe(self) -> str:
        what = "허용 항목과 조각이 딸린 정의 하나" if self.with_fragment else "정의 하나"
        return f"{what}와, {_who(self.role)}"

    @override
    async def lay(self, seeding: Any) -> ADefinitionAndACaller:
        home = await seeding.creating(SeedDomain(name_hint="home", description=WAS_HERE))
        definition = await seeding.creating(SeedDefinition())
        if self.with_fragment:
            entry = await seeding.creating_from(
                SeedAllowListEntry(scope_type=AppConfigScopeType.PUBLIC), definition
            )
            await seeding.creating_from(SeedPublicFragment(config={"theme": "light"}), entry)
        caller = await seeding.within(SomeoneOf(home, role=self.role))
        return ADefinitionAndACaller(
            domain=seeding.made(home),
            caller=seeding.made(caller),
            definition=seeding.made(definition),
        )


@dataclass(frozen=True)
class ManyDefinitionsAndACaller:
    """훑을 정의 여럿과, 훑을 사람. ``named``는 그중 골라낼 하나다."""

    caller: UserData
    laid: tuple[AppConfigDefinitionData, ...]
    named: AppConfigDefinitionData


@dataclass(frozen=True)
class ManyDefinitionsAndSomeone(Given[Any, ManyDefinitionsAndACaller]):
    """정의 여럿과, 슈퍼관리자 또는 아무 권한도 받지 않은 사용자 한 명."""

    count: int = 3
    role: UserRole = UserRole.USER

    @override
    def describe(self) -> str:
        return f"정의 {self.count}개와, {_who(self.role)}"

    @override
    async def lay(self, seeding: Any) -> ManyDefinitionsAndACaller:
        home = await seeding.creating(SeedDomain(name_hint="home", description=WAS_HERE))
        wanted = await seeding.creating(SeedDefinition(name_hint="wanted"))
        others = [
            await seeding.creating(SeedDefinition(name_hint="other")) for _ in range(self.count - 1)
        ]
        caller = await seeding.within(SomeoneOf(home, role=self.role))
        return ManyDefinitionsAndACaller(
            caller=seeding.made(caller),
            laid=tuple(seeding.made(one) for one in [wanted, *others]),
            named=seeding.made(wanted),
        )


@dataclass(frozen=True)
class TwoDefinitionsAndACaller:
    """id로 함께 읽을 정의 둘과, 읽을 사람."""

    caller: UserData
    first: AppConfigDefinitionData
    second: AppConfigDefinitionData


@dataclass(frozen=True)
class TwoDefinitionsAndSomeone(Given[Any, TwoDefinitionsAndACaller]):
    """정의 둘과, 슈퍼관리자 또는 아무 권한도 받지 않은 사용자 한 명."""

    role: UserRole = UserRole.USER

    @override
    def describe(self) -> str:
        return f"정의 둘과, {_who(self.role)}"

    @override
    async def lay(self, seeding: Any) -> TwoDefinitionsAndACaller:
        home = await seeding.creating(SeedDomain(name_hint="home", description=WAS_HERE))
        first = await seeding.creating(SeedDefinition(name_hint="first"))
        second = await seeding.creating(SeedDefinition(name_hint="second"))
        caller = await seeding.within(SomeoneOf(home, role=self.role))
        return TwoDefinitionsAndACaller(
            caller=seeding.made(caller),
            first=seeding.made(first),
            second=seeding.made(second),
        )


@dataclass(frozen=True)
class TheDefinitionNode(Then[ADefinitionAndACaller, AppConfigDefinitionNode]):
    """심은 정의가 통째로 온다."""

    started: datetime

    @override
    def says(self) -> str:
        return "심은 정의 전체가 온다"

    @override
    def look(
        self, laid: ADefinitionAndACaller, answered: Answered[AppConfigDefinitionNode]
    ) -> list[Verdict]:
        node = answered.response
        if node is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        written = WrittenByThisRun(self.started)
        return [
            Held("id", node.id, SameAs[UUID](laid.definition.id, "심은 정의")),
            Same("config_name", node.config_name, laid.definition.config_name),
            Held("created_at", node.created_at, written),
            Held("updated_at", node.updated_at, written),
        ]


@dataclass(frozen=True)
class TheNewDefinitionNode(Then[Any, AppConfigDefinitionNode]):
    """방금 등록한 정의가 통째로 온다. 이름은 시나리오가 정한 것이다."""

    started: datetime
    named: str

    @override
    def says(self) -> str:
        return "등록한 정의 전체가 온다"

    @override
    def look(self, laid: Any, answered: Answered[AppConfigDefinitionNode]) -> list[Verdict]:
        node = answered.response
        if node is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        written = WrittenByThisRun(self.started)
        return [
            Skipped("id", "데이터베이스가 만든다"),
            Same("config_name", node.config_name, self.named),
            Held("created_at", node.created_at, written),
            Held("updated_at", node.updated_at, written),
        ]


@dataclass(frozen=True)
class EveryLaidDefinitionIsFound(
    Then[ManyDefinitionsAndACaller, SearchAppConfigDefinitionsPayload]
):
    """심은 정의가 모두, 그리고 그것만 세어진다."""

    @override
    def says(self) -> str:
        return "심은 정의가 모두, 그리고 그것만 세어진다"

    @override
    def look(
        self,
        laid: ManyDefinitionsAndACaller,
        answered: Answered[SearchAppConfigDefinitionsPayload],
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
class OnlyTheNamedDefinitionIsFound(
    Then[ManyDefinitionsAndACaller, SearchAppConfigDefinitionsPayload]
):
    """골라낸 하나만 남는다."""

    @override
    def says(self) -> str:
        return "이름으로 고른 정의만 남는다"

    @override
    def look(
        self,
        laid: ManyDefinitionsAndACaller,
        answered: Answered[SearchAppConfigDefinitionsPayload],
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        return [
            Same("items", [one.config_name for one in payload.items], [laid.named.config_name]),
            Same("total_count", payload.total_count, 1),
            Same("has_next_page", payload.has_next_page, False),
            Same("has_previous_page", payload.has_previous_page, False),
        ]


@dataclass(frozen=True)
class DefinitionsComeInNameOrder(
    Then[ManyDefinitionsAndACaller, SearchAppConfigDefinitionsPayload]
):
    """이름 오름차순으로 온다."""

    @override
    def says(self) -> str:
        return "이름 순서대로 온다"

    @override
    def look(
        self,
        laid: ManyDefinitionsAndACaller,
        answered: Answered[SearchAppConfigDefinitionsPayload],
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        return [
            Same(
                "items",
                [one.config_name for one in payload.items],
                sorted(one.config_name for one in laid.laid),
            ),
            Same("total_count", payload.total_count, len(laid.laid)),
        ]


@dataclass(frozen=True)
class TenComeWithANextPage(Then[ManyDefinitionsAndACaller, SearchAppConfigDefinitionsPayload]):
    """크기를 대지 않으면 열 건까지 오고 다음 쪽이 있다고 답한다."""

    @override
    def says(self) -> str:
        return "열 건까지 오고 다음 쪽이 있다고 답한다"

    @override
    def look(
        self,
        laid: ManyDefinitionsAndACaller,
        answered: Answered[SearchAppConfigDefinitionsPayload],
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
