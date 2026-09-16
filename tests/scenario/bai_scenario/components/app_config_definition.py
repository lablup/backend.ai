"""Shared arrangements and expectations for app config definition scenarios."""

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
    return "슈퍼관리자 한 명" if role == UserRole.SUPERADMIN else "권한이 없는 일반 사용자 한 명"


@dataclass(frozen=True)
class ADefinitionAndACaller:
    """설정 정의 하나와, 그것을 호출할 사용자."""

    domain: DomainData
    caller: UserData
    definition: AppConfigDefinitionData


@dataclass(frozen=True)
class ADefinitionAndSomeone(Given[Any, ADefinitionAndACaller]):
    """설정 정의 하나와 슈퍼관리자 또는 권한이 없는 일반 사용자 한 명.

    ``with_fragment``는 그 이름에 공개 허용 목록 항목과 공개 설정 조각을 함께 만들어 둔다.
    """

    role: UserRole = UserRole.USER
    with_fragment: bool = False

    @override
    def describe(self) -> str:
        what = (
            "허용 목록 항목과 설정 조각이 딸린 설정 정의 하나"
            if self.with_fragment
            else "설정 정의 하나"
        )
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
    """검색 대상 설정 정의 여럿과, 검색을 호출할 사용자."""

    caller: UserData
    laid: tuple[AppConfigDefinitionData, ...]


@dataclass(frozen=True)
class ManyDefinitionsAndSomeone(Given[Any, ManyDefinitionsAndACaller]):
    """설정 정의 여럿과 슈퍼관리자 또는 권한이 없는 일반 사용자 한 명."""

    count: int = 3
    role: UserRole = UserRole.USER

    @override
    def describe(self) -> str:
        return f"설정 정의 {self.count}개와, {_who(self.role)}"

    @override
    async def lay(self, seeding: Any) -> ManyDefinitionsAndACaller:
        home = await seeding.creating(SeedDomain(name_hint="home", description=WAS_HERE))
        laid = [
            await seeding.creating(SeedDefinition(name_hint="definition"))
            for _ in range(self.count)
        ]
        caller = await seeding.within(SomeoneOf(home, role=self.role))
        return ManyDefinitionsAndACaller(
            caller=seeding.made(caller),
            laid=tuple(seeding.made(one) for one in laid),
        )


@dataclass(frozen=True)
class TwoDefinitionsAndACaller:
    """ID로 함께 조회할 설정 정의 둘과 조회할 사용자."""

    caller: UserData
    first: AppConfigDefinitionData
    second: AppConfigDefinitionData


@dataclass(frozen=True)
class TwoDefinitionsAndSomeone(Given[Any, TwoDefinitionsAndACaller]):
    """설정 정의 둘과 슈퍼관리자 또는 권한이 없는 일반 사용자 한 명."""

    role: UserRole = UserRole.USER

    @override
    def describe(self) -> str:
        return f"설정 정의 둘과, {_who(self.role)}"

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
    """미리 만들어 둔 설정 정의의 모든 필드가 반환된다."""

    started: datetime

    @override
    def says(self) -> str:
        return "미리 만들어 둔 설정 정의의 모든 필드가 반환된다"

    @override
    def look(
        self, laid: ADefinitionAndACaller, answered: Answered[AppConfigDefinitionNode]
    ) -> list[Verdict]:
        node = answered.response
        if node is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        written = WrittenByThisRun(self.started)
        return [
            Held("ID", node.id, SameAs[UUID](laid.definition.id, "미리 만들어 둔 설정 정의")),
            Same("config_name", node.config_name, laid.definition.config_name),
            Held("created_at", node.created_at, written),
            Held("updated_at", node.updated_at, written),
        ]


@dataclass(frozen=True)
class TheNewDefinitionNode(Then[Any, AppConfigDefinitionNode]):
    """방금 등록한 설정 정의의 모든 필드가 반환된다."""

    started: datetime
    named: str

    @override
    def says(self) -> str:
        return "등록한 설정 정의의 모든 필드가 반환된다"

    @override
    def look(self, laid: Any, answered: Answered[AppConfigDefinitionNode]) -> list[Verdict]:
        node = answered.response
        if node is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        written = WrittenByThisRun(self.started)
        return [
            Skipped("ID", "데이터베이스가 만든다"),
            Same("config_name", node.config_name, self.named),
            Held("created_at", node.created_at, written),
            Held("updated_at", node.updated_at, written),
        ]


@dataclass(frozen=True)
class EveryLaidDefinitionIsFound(
    Then[ManyDefinitionsAndACaller, SearchAppConfigDefinitionsPayload]
):
    """미리 만들어 둔 설정 정의가 모두, 그리고 그것만 집계된다."""

    @override
    def says(self) -> str:
        return "미리 만들어 둔 설정 정의가 모두, 그리고 그것만 집계된다"

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
