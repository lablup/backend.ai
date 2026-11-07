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

from ai.backend.common.data.entity.global_entity import GlobalEntityName
from ai.backend.common.data.entity.prometheus_query_preset_category import (
    PrometheusQueryPresetCategoryEntityType,
)
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.common import PartialBulkPayload
from ai.backend.common.dto.manager.v2.prometheus_query_preset_category.response import (
    CategoryNode,
    DeleteCategoryPayload,
    SearchCategoriesPayload,
)
from ai.backend.manager.data.permission.global_entity import global_entity_id
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.data.prometheus_query_preset_category.types import (
    PrometheusQueryPresetCategoryData,
)
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.errors.user import UserNotFound
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    Refused,
    Same,
    SameAs,
    Says,
    Skipped,
    Then,
    Verdict,
)
from bai_scenario.components.domain import WAS_HERE, Mentions, SomeoneOf, WrittenByThisRun
from bai_scenario.components.system import lay_a_public_reader
from bai_scenario.seeds.domain.domain import TestSeedDomain
from bai_scenario.seeds.prometheus_query_preset_category.category import TestSeedCategory
from bai_scenario.seeds.rbac.role import TestSeedPermission, TestSeedRole
from bai_scenario.seeds.seeder import Laid, TestSeeder, TestSeedNest

type CategoryNodeAnswer = CategoryNode | None
"""The get payload may carry no node, so every step answering a node is typed by this."""

type LoadedCategory = CategoryNode | Exception | None
"""What the batch read answers per id: the node, a denial, or nothing."""

PAGE = 10
"""How many a search answers when the request names no page size."""


@dataclass(frozen=True)
class ACallerAlone:
    """호출자 한 명."""

    caller: UserData


@dataclass(frozen=True)
class ACategoryAndACaller:
    """이미 있는 카테고리 하나와, 그것을 호출할 사용자."""

    category: PrometheusQueryPresetCategoryData
    caller: UserData


@dataclass(frozen=True)
class ACategoryAlone:
    """카테고리 하나뿐이고, 호출자가 없다."""

    category: PrometheusQueryPresetCategoryData


@dataclass(frozen=True)
class ManyCategoriesAndACaller:
    """검색 대상 카테고리 여럿과, 검색을 호출할 사용자. ``named``는 그중 이름 필터로 골라낼 하나다."""

    laid: tuple[PrometheusQueryPresetCategoryData, ...]
    named: PrometheusQueryPresetCategoryData
    caller: UserData


@dataclass(frozen=True)
class SomeoneGrantedOnCategories(TestSeedNest[Laid[UserData]]):
    """global 에서 카테고리에 대한 권한을 받은 사용자."""

    domain: Laid[Any]
    granted: tuple[Permission, ...]
    role: UserRole = UserRole.USER

    @override
    def kind(self) -> str:
        return Says(
            "global 에서 카테고리 권한을 받은 사용자 준비",
            english="Prepare a user granted permission on categories in global",
        )

    @override
    def lay(self, seed: TestSeeder) -> Laid[UserData]:
        someone = seed.within(SomeoneOf(self.domain, role=self.role))
        granted_role = seed.creating_from(
            TestSeedRole(
                lambda _: global_entity_id(GlobalEntityName.GLOBAL), name_hint="category-keeper"
            ),
            someone,
        )
        for permission in self.granted:
            seed.adding(
                TestSeedPermission(
                    entity_type=PrometheusQueryPresetCategoryEntityType(), permission=permission
                ),
                granted_role,
            )
        seed.granting(granted_role, someone, role_id=lambda r: r.id, user_id=lambda u: UserID(u.id))
        return someone


async def lay_someone(
    seeding: Any, role: UserRole, granted: tuple[Permission, ...] = ()
) -> Laid[UserData]:
    """호출자 한 명. `granted`가 없으면 public 에서 읽을 권한을 함께 받는다."""
    if granted:
        home = await seeding.creating(TestSeedDomain(name_hint="home", description=WAS_HERE))
        return await seeding.within(SomeoneGrantedOnCategories(home, granted, role=role))
    return await lay_a_public_reader(seeding, PrometheusQueryPresetCategoryEntityType(), role)


@dataclass(frozen=True)
class JustSomeone(Given[Any, ACallerAlone]):
    """카테고리가 하나도 없고, 호출자 한 명."""

    role: UserRole = UserRole.USER

    @override
    def describe(self) -> str:
        return Says(
            f"카테고리가 하나도 없고, {self.role.value} 한 명",
            english=f"no category and one {self.role.value}",
        )

    @override
    async def lay(self, seeding: Any) -> ACallerAlone:
        caller = await lay_someone(seeding, self.role)
        return ACallerAlone(caller=seeding.made(caller))


@dataclass(frozen=True)
class ACategoryAndSomeone(Given[Any, ACategoryAndACaller]):
    """이미 있는 카테고리 하나와, 호출자 한 명."""

    role: UserRole = UserRole.USER

    @override
    def describe(self) -> str:
        return Says(
            f"이미 있는 카테고리 하나와, {self.role.value} 한 명",
            english=f"one existing category and one {self.role.value}",
        )

    @override
    async def lay(self, seeding: Any) -> ACategoryAndACaller:
        category = await seeding.creating(TestSeedCategory())
        caller = await lay_someone(seeding, self.role)
        return ACategoryAndACaller(category=seeding.made(category), caller=seeding.made(caller))


@dataclass(frozen=True)
class ACategoryAndNobody(Given[Any, ACategoryAlone]):
    """카테고리 하나뿐이고, 호출자는 없다."""

    @override
    def describe(self) -> str:
        return Says(
            "이미 있는 카테고리 하나, 호출자 없음",
            english="one existing category and no caller",
        )

    @override
    async def lay(self, seeding: Any) -> ACategoryAlone:
        category = await seeding.creating(TestSeedCategory())
        return ACategoryAlone(category=seeding.made(category))


@dataclass(frozen=True)
class ManyCategoriesAndSomeone(Given[Any, ManyCategoriesAndACaller]):
    """카테고리 여럿과, 호출자 한 명. `granted`가 있으면 global 에서 그 권한을 받는다."""

    role: UserRole = UserRole.USER
    besides: int = 1
    granted: tuple[Permission, ...] = ()

    @override
    def describe(self) -> str:
        if self.granted:
            permissions = ", ".join(one.name for one in self.granted)
            return Says(
                f"카테고리 {self.besides + 1}개와, global 에서 {permissions} 권한을 받은 "
                "일반 사용자 한 명",
                english=(
                    f"{self.besides + 1} categories and one regular user granted "
                    f"{permissions} in global"
                ),
            )
        return Says(
            f"카테고리 {self.besides + 1}개와, {self.role.value} 한 명",
            english=f"{self.besides + 1} categories and one {self.role.value}",
        )

    @override
    async def lay(self, seeding: Any) -> ManyCategoriesAndACaller:
        wanted = await seeding.creating(TestSeedCategory(name_hint="wanted"))
        others = [
            await seeding.creating(TestSeedCategory(name_hint="other")) for _ in range(self.besides)
        ]
        caller = await lay_someone(seeding, self.role, self.granted)
        return ManyCategoriesAndACaller(
            laid=tuple(seeding.made(one) for one in [wanted, *others]),
            named=seeding.made(wanted),
            caller=seeding.made(caller),
        )


@dataclass(frozen=True)
class TheNewCategoryNode(Then[Any, CategoryNodeAnswer]):
    """방금 생성한 카테고리가 통째로 반환된다. 이름과 설명은 시나리오가 정한 값이다."""

    started: datetime
    named: str
    described: str | None

    @override
    def says(self) -> str:
        return Says(
            "생성한 카테고리 전체가 반환됩니다",
            english="the whole category just created comes back",
        )

    @override
    def look(self, laid: Any, answered: Answered[CategoryNodeAnswer]) -> list[Verdict]:
        node = answered.response
        if node is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        written = WrittenByThisRun(self.started)
        return [
            Skipped("id", Says("데이터베이스가 생성합니다", english="the database generates it")),
            Same("name", node.name, self.named),
            Same("description", node.description, self.described),
            Held("created_at", node.created_at, written),
            Held("updated_at", node.updated_at, written),
        ]


@dataclass(frozen=True)
class TheCategoryNode(Then[ACategoryAndACaller, CategoryNodeAnswer]):
    """미리 만들어 둔 카테고리가 통째로 반환된다. 기대값은 미리 만들어 둔 데이터에서 읽는다."""

    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "미리 저장한 카테고리 전체가 반환됩니다",
            english="the whole category seeded in advance comes back",
        )

    @override
    def look(
        self, laid: ACategoryAndACaller, answered: Answered[CategoryNodeAnswer]
    ) -> list[Verdict]:
        node = answered.response
        if node is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        written = WrittenByThisRun(self.started)
        return [
            Held(
                "id",
                node.id,
                SameAs[UUID](
                    laid.category.id,
                    Says("미리 저장한 카테고리", english="the category seeded in advance"),
                ),
            ),
            Same("name", node.name, laid.category.name),
            Same("description", node.description, laid.category.description),
            Held("created_at", node.created_at, written),
            Held("updated_at", node.updated_at, written),
        ]


@dataclass(frozen=True)
class EveryLaidCategoryIsFound(Then[ManyCategoriesAndACaller, SearchCategoriesPayload]):
    """미리 만들어 둔 카테고리가 모두, 그리고 그것만 집계된다."""

    @override
    def says(self) -> str:
        return Says(
            "미리 저장한 카테고리가 모두, 그리고 그것만 집계됩니다",
            english="every category seeded in advance is counted, and only those",
        )

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
    """크기를 지정하지 않은 검색은 한 페이지 분량만 응답하고, 다음 페이지가 있다고 알린다."""

    @override
    def says(self) -> str:
        return Says(
            "한 페이지만 반환되고 다음 페이지가 있다고 응답합니다",
            english="one page comes back and the response says there is a next page",
        )

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
        entity_id=seeded.id,
        name=seeded.name,
        description=seeded.description,
        created_at=seeded.created_at,
        updated_at=seeded.updated_at,
    )


@dataclass(frozen=True)
class TheBatchAnswersInOrder(Then[ManyCategoriesAndACaller, list[LoadedCategory]]):
    """요청한 순서대로 응답한다. 미리 만들어 둔 것은 노드 전체로, 마지막의 없는 id는 거부로."""

    @override
    def says(self) -> str:
        return Says(
            "요청한 순서대로 반환되고, 없는 id 에 해당하는 항목은 거부가 담깁니다",
            english=(
                "the items come back in the order requested and the item for an unknown id "
                "carries a denial"
            ),
        )

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
                    SameAs[LoadedCategory](
                        node_of(wanted),
                        Says(
                            f"{at + 1}번째로 요청한 id 의 카테고리 전체",
                            english=(
                                f"the whole category of the id requested at position {at + 1}"
                            ),
                        ),
                    ),
                )
            )
        last = answer[-1]
        seen.append(Refused(NotEnoughPermission, last if isinstance(last, BaseException) else None))
        return seen


@dataclass(frozen=True)
class NothingIsAnswered(Then[Any, list[LoadedCategory]]):
    """빈 목록에는 빈 응답이다."""

    @override
    def says(self) -> str:
        return Says("빈 응답이 반환됩니다", english="an empty response comes back")

    @override
    def look(self, laid: Any, answered: Answered[list[LoadedCategory]]) -> list[Verdict]:
        answer = answered.response
        if answer is None:
            return [Refused(UserNotFound, answered.raised)]
        return [Same("answer", answer, [])]


@dataclass(frozen=True)
class TheRemovedOneIsNamed(Then[ACategoryAndACaller, DeleteCategoryPayload]):
    """삭제한 카테고리가 무엇인지 응답한다."""

    @override
    def says(self) -> str:
        return Says(
            "삭제한 카테고리를 응답합니다",
            english="the response names the category that was deleted",
        )

    @override
    def look(
        self, laid: ACategoryAndACaller, answered: Answered[DeleteCategoryPayload]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        return [
            Held(
                "id",
                payload.id,
                SameAs[UUID](
                    laid.category.id,
                    Says("미리 저장한 카테고리", english="the category seeded in advance"),
                ),
            )
        ]


@dataclass(frozen=True)
class NothingIsProcessed(Then[ManyCategoriesAndACaller, PartialBulkPayload[CategoryNode]]):
    """처리된 카테고리 없이, 미리 만들어 둔 카테고리가 모두 같은 이유로 실패 목록에 온다."""

    reason: str

    @override
    def says(self) -> str:
        return Says(
            "처리된 카테고리 없이 대상이 모두 실패 목록에 옵니다",
            english="no category is processed and every target comes back in the failed list",
        )

    @override
    def look(
        self,
        laid: ManyCategoriesAndACaller,
        answered: Answered[PartialBulkPayload[CategoryNode]],
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        verdicts: list[Verdict] = [
            Same("successes", payload.successes, []),
            Same("failed count", len(payload.failed), len(laid.laid)),
        ]
        for i, (failure, one) in enumerate(zip(payload.failed, laid.laid, strict=False)):
            verdicts += [
                Held[UUID](
                    f"failed[{i}].id",
                    failure.id,
                    SameAs(
                        one.id,
                        Says("대상 카테고리의 id", english="the id of the target category"),
                    ),
                ),
                Held(f"failed[{i}].message", failure.message, Mentions(self.reason)),
            ]
        return verdicts
