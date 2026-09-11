"""What a query preset category scenario table says besides the call.

A category is a name presets are filed under, in a global catalog nothing scopes. The
presets pointing at one are laid by the preset table; this one lays categories and a
caller.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, override
from uuid import UUID

from bai_scenario.components.domain import WAS_HERE, SomeoneOf, WrittenByThisRun
from bai_scenario.seeds.domain.domain import SeedDomain
from bai_scenario.seeds.prometheus_query_preset_category.category import SeedCategory
from bai_scenario.seeds.seeder import Laid

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.prometheus_query_preset_category.response import (
    CategoryNode,
    DeleteCategoryPayload,
    SearchCategoriesPayload,
)
from ai.backend.manager.data.prometheus_query_preset_category.types import (
    PrometheusQueryPresetCategoryData,
)
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.errors.user import UserNotFound
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

type CategoryNodeAnswer = CategoryNode | None
"""The get payload may carry no node, so every step answering a node is typed by this."""

type LoadedCategory = CategoryNode | Exception | None
"""What the batch read answers per id: the node, a denial, or nothing."""

PAGE = 10
"""How many a search answers when the request names no page size."""


@dataclass(frozen=True)
class ACallerAlone:
    """부를 사람 한 명."""

    caller: UserData


@dataclass(frozen=True)
class ACategoryAndACaller:
    """이미 있는 분류 하나와, 그것을 부를 사람."""

    category: PrometheusQueryPresetCategoryData
    caller: UserData


@dataclass(frozen=True)
class ACategoryAlone:
    """분류 하나뿐, 부를 사람이 없다."""

    category: PrometheusQueryPresetCategoryData


@dataclass(frozen=True)
class ManyCategoriesAndACaller:
    """훑을 분류 여럿과, 훑을 사람. ``named``는 그중 골라낼 하나다."""

    laid: tuple[PrometheusQueryPresetCategoryData, ...]
    named: PrometheusQueryPresetCategoryData
    caller: UserData


async def lay_someone(seeding: Any, role: UserRole) -> Laid[UserData]:
    """부를 사람 한 명. 사용자는 도메인에 속해야 하므로 도메인 하나가 함께 깔린다."""
    domain = await seeding.creating(SeedDomain(name_hint="home", description=WAS_HERE))
    laid: Laid[UserData] = await seeding.within(SomeoneOf(domain, role=role))
    return laid


@dataclass(frozen=True)
class JustSomeone(Given[Any, ACallerAlone]):
    """분류가 하나도 없고, 부를 사람 한 명."""

    role: UserRole = UserRole.USER

    @override
    def describe(self) -> str:
        return f"분류가 하나도 없고, {self.role.value} 한 명"

    @override
    async def lay(self, seeding: Any) -> ACallerAlone:
        caller = await lay_someone(seeding, self.role)
        return ACallerAlone(caller=seeding.made(caller))


@dataclass(frozen=True)
class ACategoryAndSomeone(Given[Any, ACategoryAndACaller]):
    """이미 있는 분류 하나와, 부를 사람 한 명."""

    role: UserRole = UserRole.USER

    @override
    def describe(self) -> str:
        return f"이미 있는 분류 하나와, {self.role.value} 한 명"

    @override
    async def lay(self, seeding: Any) -> ACategoryAndACaller:
        category = await seeding.creating(SeedCategory())
        caller = await lay_someone(seeding, self.role)
        return ACategoryAndACaller(category=seeding.made(category), caller=seeding.made(caller))


@dataclass(frozen=True)
class ACategoryAndNobody(Given[Any, ACategoryAlone]):
    """분류 하나뿐이고, 부를 사람은 없다."""

    @override
    def describe(self) -> str:
        return "이미 있는 분류 하나, 부를 사람 없음"

    @override
    async def lay(self, seeding: Any) -> ACategoryAlone:
        category = await seeding.creating(SeedCategory())
        return ACategoryAlone(category=seeding.made(category))


@dataclass(frozen=True)
class ManyCategoriesAndSomeone(Given[Any, ManyCategoriesAndACaller]):
    """분류 여럿과, 부를 사람 한 명."""

    role: UserRole = UserRole.USER
    besides: int = 1

    @override
    def describe(self) -> str:
        return f"분류 {self.besides + 1}개와, {self.role.value} 한 명"

    @override
    async def lay(self, seeding: Any) -> ManyCategoriesAndACaller:
        wanted = await seeding.creating(SeedCategory(name_hint="wanted"))
        others = [
            await seeding.creating(SeedCategory(name_hint="other")) for _ in range(self.besides)
        ]
        caller = await lay_someone(seeding, self.role)
        return ManyCategoriesAndACaller(
            laid=tuple(seeding.made(one) for one in [wanted, *others]),
            named=seeding.made(wanted),
            caller=seeding.made(caller),
        )


@dataclass(frozen=True)
class TheNewCategoryNode(Then[Any, CategoryNodeAnswer]):
    """방금 만든 분류가 통째로 온다. 이름과 설명은 시나리오가 정한 것이다."""

    started: datetime
    named: str
    described: str | None

    @override
    def says(self) -> str:
        return "만든 분류 전체가 온다"

    @override
    def look(self, laid: Any, answered: Answered[CategoryNodeAnswer]) -> list[Verdict]:
        node = answered.response
        if node is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        written = WrittenByThisRun(self.started)
        return [
            Skipped("id", "데이터베이스가 만든다"),
            Same("name", node.name, self.named),
            Same("description", node.description, self.described),
            Held("created_at", node.created_at, written),
            Held("updated_at", node.updated_at, written),
        ]


@dataclass(frozen=True)
class TheCategoryNode(Then[ACategoryAndACaller, CategoryNodeAnswer]):
    """심은 분류가 통째로 온다. 값은 심은 것에서 읽는다."""

    started: datetime

    @override
    def says(self) -> str:
        return "심은 분류 전체가 온다"

    @override
    def look(
        self, laid: ACategoryAndACaller, answered: Answered[CategoryNodeAnswer]
    ) -> list[Verdict]:
        node = answered.response
        if node is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        written = WrittenByThisRun(self.started)
        return [
            Held("id", node.id, SameAs[UUID](laid.category.id, "심은 분류")),
            Same("name", node.name, laid.category.name),
            Same("description", node.description, laid.category.description),
            Held("created_at", node.created_at, written),
            Held("updated_at", node.updated_at, written),
        ]


@dataclass(frozen=True)
class EveryLaidCategoryIsFound(Then[ManyCategoriesAndACaller, SearchCategoriesPayload]):
    """심은 분류가 모두, 그리고 그것만 세어진다."""

    @override
    def says(self) -> str:
        return "심은 분류가 모두, 그리고 그것만 세어진다"

    @override
    def look(
        self, laid: ManyCategoriesAndACaller, answered: Answered[SearchCategoriesPayload]
    ) -> list[Verdict]:
        page = answered.response
        if page is None:
            return [Refused(UserNotFound, answered.raised)]
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
class OnePageOfThemComesBack(Then[ManyCategoriesAndACaller, SearchCategoriesPayload]):
    """크기를 대지 않은 훑기는 한 쪽 분량만 답하고, 다음 쪽이 있다고 말한다."""

    @override
    def says(self) -> str:
        return "한 쪽만 오고 다음 쪽이 있다고 답한다"

    @override
    def look(
        self, laid: ManyCategoriesAndACaller, answered: Answered[SearchCategoriesPayload]
    ) -> list[Verdict]:
        page = answered.response
        if page is None:
            return [Refused(UserNotFound, answered.raised)]
        return [
            Same("items", len(page.items), PAGE),
            Same("total_count", page.total_count, len(laid.laid)),
            Same("has_next_page", page.has_next_page, True),
            Same("has_previous_page", page.has_previous_page, False),
        ]


def node_of(seeded: PrometheusQueryPresetCategoryData) -> CategoryNode:
    """The node a read of this seeded category has to answer, whole."""
    return CategoryNode(
        id=seeded.id,
        name=seeded.name,
        description=seeded.description,
        created_at=seeded.created_at,
        updated_at=seeded.updated_at,
    )


@dataclass(frozen=True)
class TheBatchAnswersInOrder(Then[ManyCategoriesAndACaller, list[LoadedCategory]]):
    """준 순서대로 답한다. 심은 것은 노드 전체로, 마지막의 없는 id는 빈 자리로."""

    @override
    def says(self) -> str:
        return "준 순서대로, 없는 id 자리는 비어서 온다"

    @override
    def look(
        self, laid: ManyCategoriesAndACaller, answered: Answered[list[LoadedCategory]]
    ) -> list[Verdict]:
        answer = answered.response
        if answer is None:
            return [Refused(UserNotFound, answered.raised)]
        seen: list[Verdict] = [Same("len", len(answer), len(laid.laid) + 1)]
        if len(answer) != len(laid.laid) + 1:
            return seen
        for at, (got, wanted) in enumerate(zip(answer, laid.laid, strict=False)):
            seen.append(
                Held(
                    f"[{at}]",
                    got,
                    SameAs[LoadedCategory](node_of(wanted), f"{at + 1}번째로 준 id의 분류 전체"),
                )
            )
        seen.append(Same(f"[{len(laid.laid)}]", answer[-1], None))
        return seen


@dataclass(frozen=True)
class NothingIsAnswered(Then[Any, list[LoadedCategory]]):
    """빈 목록에는 빈 답이다."""

    @override
    def says(self) -> str:
        return "빈 답이 온다"

    @override
    def look(self, laid: Any, answered: Answered[list[LoadedCategory]]) -> list[Verdict]:
        answer = answered.response
        if answer is None:
            return [Refused(UserNotFound, answered.raised)]
        return [Same("answer", answer, [])]


@dataclass(frozen=True)
class TheRemovedOneIsNamed(Then[ACategoryAndACaller, DeleteCategoryPayload]):
    """지운 분류가 무엇인지 답한다."""

    @override
    def says(self) -> str:
        return "지운 분류를 답한다"

    @override
    def look(
        self, laid: ACategoryAndACaller, answered: Answered[DeleteCategoryPayload]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        return [Held("id", payload.id, SameAs[UUID](laid.category.id, "심은 분류"))]
