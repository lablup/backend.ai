"""What a query preset scenario table says besides the call.

A preset lives in a global catalog: nothing scopes it, so a table lays the preset and a
caller side by side and never a role between them. The category a preset is filed
under is laid here too, because a preset row names one; the category's own calls have
a table of their own.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any, override
from uuid import UUID

from bai_scenario.components.domain import WAS_HERE, SomeoneOf, WrittenByThisRun
from bai_scenario.fakes.prometheus import ANSWERED_AT, INSTANT
from bai_scenario.seeds.domain.domain import SeedDomain
from bai_scenario.seeds.prometheus_query_preset.category import SeedCategory
from bai_scenario.seeds.prometheus_query_preset.preset import (
    METRIC,
    TEMPLATE,
    SeedPreset,
    SeedPresetIn,
)
from bai_scenario.seeds.seeder import Laid

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.prometheus_query_preset.response import (
    DeleteQueryDefinitionPayload,
    QueryDefinitionNode,
    QueryDefinitionResultInfo,
    SearchQueryDefinitionsPayload,
)
from ai.backend.common.dto.manager.v2.prometheus_query_preset.types import (
    QueryDefinitionOptionsInfo,
)
from ai.backend.common.exception import PrometheusQueryPresetNotFound
from ai.backend.manager.data.prometheus_query_preset.types import PrometheusQueryPresetData
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

type PresetNodeAnswer = QueryDefinitionNode | None
"""The get payload may carry no node, so every step answering a node is typed by this."""

PAGE = 10
"""How many a search answers when the request names no page size."""


@dataclass(frozen=True)
class ACatalogAndACaller:
    """호출자 한 명과, 있다면 프리셋을 넣을 카테고리 하나."""

    caller: UserData
    category: PrometheusQueryPresetCategoryData | None = None


@dataclass(frozen=True)
class APresetAndACaller:
    """이미 있는 프리셋 하나와, 그것을 호출할 사용자. ``elsewhere``는 옮겨 갈 다른 카테고리다."""

    preset: PrometheusQueryPresetData
    caller: UserData
    elsewhere: PrometheusQueryPresetCategoryData | None = None


@dataclass(frozen=True)
class APresetAlone:
    """프리셋 하나뿐이고, 호출자가 없다."""

    preset: PrometheusQueryPresetData


@dataclass(frozen=True)
class ManyPresetsAndACaller:
    """검색 대상 프리셋 여럿과, 검색을 호출할 사용자. ``named``는 그중 이름 필터로 골라낼 하나, ``category``는 필터로 쓸 카테고리다."""

    laid: tuple[PrometheusQueryPresetData, ...]
    named: PrometheusQueryPresetData
    caller: UserData
    category: PrometheusQueryPresetCategoryData | None = None


async def lay_someone(seeding: Any, role: UserRole) -> Laid[UserData]:
    """호출자 한 명. 사용자는 도메인에 속해야 하므로 도메인 하나를 함께 만든다."""
    domain = await seeding.creating(SeedDomain(name_hint="home", description=WAS_HERE))
    laid: Laid[UserData] = await seeding.within(SomeoneOf(domain, role=role))
    return laid


@dataclass(frozen=True)
class JustSomeone(Given[Any, ACatalogAndACaller]):
    """프리셋도 카테고리도 없이, 호출자 한 명."""

    role: UserRole = UserRole.USER

    @override
    def describe(self) -> str:
        return f"프리셋이 하나도 없고, {self.role.value} 한 명"

    @override
    async def lay(self, seeding: Any) -> ACatalogAndACaller:
        caller = await lay_someone(seeding, self.role)
        return ACatalogAndACaller(caller=seeding.made(caller))


@dataclass(frozen=True)
class ACategoryAndSomeone(Given[Any, ACatalogAndACaller]):
    """카테고리 하나와, 호출자 한 명."""

    role: UserRole = UserRole.USER

    @override
    def describe(self) -> str:
        return f"카테고리 하나와, {self.role.value} 한 명"

    @override
    async def lay(self, seeding: Any) -> ACatalogAndACaller:
        category = await seeding.creating(SeedCategory())
        caller = await lay_someone(seeding, self.role)
        return ACatalogAndACaller(caller=seeding.made(caller), category=seeding.made(category))


@dataclass(frozen=True)
class APresetAndSomeone(Given[Any, APresetAndACaller]):
    """이미 있는 프리셋 하나와, 호출자 한 명."""

    role: UserRole = UserRole.USER
    query_template: str = TEMPLATE
    time_window: str | None = None
    filter_labels: Sequence[str] = ()
    group_labels: Sequence[str] = ()

    @override
    def describe(self) -> str:
        return f"이미 있는 프리셋 하나와, {self.role.value} 한 명"

    @override
    async def lay(self, seeding: Any) -> APresetAndACaller:
        preset = await seeding.creating(
            SeedPreset(
                query_template=self.query_template,
                time_window=self.time_window,
                filter_labels=self.filter_labels,
                group_labels=self.group_labels,
            )
        )
        caller = await lay_someone(seeding, self.role)
        return APresetAndACaller(preset=seeding.made(preset), caller=seeding.made(caller))


@dataclass(frozen=True)
class APresetInOneOfTwoCategories(Given[Any, APresetAndACaller]):
    """카테고리 둘과 한쪽에 속한 프리셋 하나, 그리고 호출자 한 명."""

    role: UserRole = UserRole.USER

    @override
    def describe(self) -> str:
        return f"카테고리 둘과 한쪽에 속한 프리셋 하나, {self.role.value} 한 명"

    @override
    async def lay(self, seeding: Any) -> APresetAndACaller:
        home = await seeding.creating(SeedCategory(name_hint="home"))
        elsewhere = await seeding.creating(SeedCategory(name_hint="elsewhere"))
        preset = await seeding.creating_from(SeedPresetIn(), home)
        caller = await lay_someone(seeding, self.role)
        return APresetAndACaller(
            preset=seeding.made(preset),
            caller=seeding.made(caller),
            elsewhere=seeding.made(elsewhere),
        )


@dataclass(frozen=True)
class APresetAndNobody(Given[Any, APresetAlone]):
    """프리셋 하나뿐이고, 호출자는 없다."""

    @override
    def describe(self) -> str:
        return "이미 있는 프리셋 하나, 호출자 없음"

    @override
    async def lay(self, seeding: Any) -> APresetAlone:
        preset = await seeding.creating(SeedPreset())
        return APresetAlone(preset=seeding.made(preset))


@dataclass(frozen=True)
class ManyPresetsAndSomeone(Given[Any, ManyPresetsAndACaller]):
    """프리셋 여럿과, 호출자 한 명."""

    role: UserRole = UserRole.USER
    besides: int = 1

    @override
    def describe(self) -> str:
        return f"프리셋 {self.besides + 1}개와, {self.role.value} 한 명"

    @override
    async def lay(self, seeding: Any) -> ManyPresetsAndACaller:
        wanted = await seeding.creating(SeedPreset(name_hint="wanted"))
        others = [
            await seeding.creating(SeedPreset(name_hint="other")) for _ in range(self.besides)
        ]
        caller = await lay_someone(seeding, self.role)
        return ManyPresetsAndACaller(
            laid=tuple(seeding.made(one) for one in [wanted, *others]),
            named=seeding.made(wanted),
            caller=seeding.made(caller),
        )


@dataclass(frozen=True)
class PresetsInTwoCategories(Given[Any, ManyPresetsAndACaller]):
    """두 카테고리에 나뉜 프리셋들과, 호출자 한 명.

    반환하는 ``laid``는 ``category``에 속한 것뿐이다. 다른 카테고리의 프리셋은 만들어 두기만
    하고 반환하지 않으므로, 필터 검색 결과에 섞여 나오면 그 자리에서 불일치가 드러난다.
    """

    role: UserRole = UserRole.USER

    @override
    def describe(self) -> str:
        return f"두 카테고리에 나뉜 프리셋 셋과, {self.role.value} 한 명"

    @override
    async def lay(self, seeding: Any) -> ManyPresetsAndACaller:
        wanted = await seeding.creating(SeedCategory(name_hint="wanted"))
        other = await seeding.creating(SeedCategory(name_hint="other"))
        first = await seeding.creating_from(SeedPresetIn(SeedPreset(name_hint="wanted")), wanted)
        second = await seeding.creating_from(SeedPresetIn(SeedPreset(name_hint="beside")), wanted)
        await seeding.creating_from(SeedPresetIn(SeedPreset(name_hint="elsewhere")), other)
        caller = await lay_someone(seeding, self.role)
        return ManyPresetsAndACaller(
            laid=(seeding.made(first), seeding.made(second)),
            named=seeding.made(first),
            caller=seeding.made(caller),
            category=seeding.made(wanted),
        )


@dataclass(frozen=True)
class TheNewPresetNode(Then[Any, PresetNodeAnswer]):
    """방금 생성한 프리셋이 통째로 반환된다. 기대값은 요청이 지정한 값에서 읽는다.

    이름을 지정하지 않으면 미리 만들어 둔 프리셋의 이름을 기대한다. 같은 이름으로 다시 생성하는
    시나리오가 그렇다.
    """

    started: datetime
    named: str | None
    query_template: str = TEMPLATE
    described: str | None = None
    time_window: str | None = None
    filter_labels: Sequence[str] = ()
    group_labels: Sequence[str] = ()
    under_the_category: bool = False

    @override
    def says(self) -> str:
        return "생성한 프리셋 전체가 반환된다"

    @override
    def look(self, laid: Any, answered: Answered[PresetNodeAnswer]) -> list[Verdict]:
        node = answered.response
        if node is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        written = WrittenByThisRun(self.started)
        category: Verdict = (
            Held(
                "category_id",
                node.category_id,
                SameAs[UUID | None](laid.category.id, "미리 만들어 둔 카테고리"),
            )
            if self.under_the_category
            else Same("category_id", node.category_id, None)
        )
        return [
            Skipped("id", "데이터베이스가 만든다"),
            Same("name", node.name, self.named if self.named is not None else laid.preset.name),
            Same("description", node.description, self.described),
            Same("rank", node.rank, 0),
            category,
            Same("metric_name", node.metric_name, METRIC),
            Same("query_template", node.query_template, self.query_template),
            Same("time_window", node.time_window, self.time_window),
            Same("options.filter_labels", node.options.filter_labels, list(self.filter_labels)),
            Same("options.group_labels", node.options.group_labels, list(self.group_labels)),
            Held("created_at", node.created_at, written),
            Held("updated_at", node.updated_at, written),
        ]


@dataclass(frozen=True)
class ThePresetNode(Then[APresetAndACaller, PresetNodeAnswer]):
    """미리 만들어 둔 프리셋이 통째로 반환된다. 기대값은 미리 만들어 둔 데이터에서 읽는다.

    수정 요청이 이 검사를 쓸 때는 바뀌어야 하는 필드만 인자로 받는다. 나머지 필드가 함께 바뀌면
    그 필드에서 불일치가 드러난다.
    """

    started: datetime
    named: str | None = None
    query_template: str | None = None
    description_cleared: bool = False
    moved_elsewhere: bool = False
    filter_labels: Sequence[str] | None = None

    @override
    def says(self) -> str:
        return "미리 만들어 둔 프리셋 전체가 반환된다"

    def _category_seen(self, got: UUID | None, laid: APresetAndACaller) -> Verdict:
        if self.moved_elsewhere and laid.elsewhere is not None:
            return Held("category_id", got, SameAs[UUID | None](laid.elsewhere.id, "다른 카테고리"))
        if laid.preset.category_id is None:
            return Same("category_id", got, None)
        return Held(
            "category_id",
            got,
            SameAs[UUID | None](laid.preset.category_id, "미리 만들어 둔 카테고리"),
        )

    @override
    def look(self, laid: APresetAndACaller, answered: Answered[PresetNodeAnswer]) -> list[Verdict]:
        node = answered.response
        if node is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        seeded = laid.preset
        written = WrittenByThisRun(self.started)
        return [
            Held("id", node.id, SameAs[UUID](seeded.id, "미리 만들어 둔 프리셋")),
            Same("name", node.name, self.named if self.named is not None else seeded.name),
            Same(
                "description",
                node.description,
                None if self.description_cleared else seeded.description,
            ),
            Same("rank", node.rank, seeded.rank),
            self._category_seen(node.category_id, laid),
            Same("metric_name", node.metric_name, seeded.metric_name),
            Same(
                "query_template",
                node.query_template,
                self.query_template if self.query_template is not None else seeded.query_template,
            ),
            Same("time_window", node.time_window, seeded.time_window),
            Same(
                "options.filter_labels",
                node.options.filter_labels,
                list(self.filter_labels)
                if self.filter_labels is not None
                else seeded.filter_labels,
            ),
            Same("options.group_labels", node.options.group_labels, seeded.group_labels),
            Held("created_at", node.created_at, written),
            Held("updated_at", node.updated_at, written),
        ]


@dataclass(frozen=True)
class EveryLaidPresetIsFound(Then[ManyPresetsAndACaller, SearchQueryDefinitionsPayload]):
    """미리 만들어 둔 프리셋이 모두, 그리고 그것만 집계된다."""

    @override
    def says(self) -> str:
        return "미리 만들어 둔 프리셋이 모두, 그리고 그것만 집계된다"

    @override
    def look(
        self, laid: ManyPresetsAndACaller, answered: Answered[SearchQueryDefinitionsPayload]
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
class OnePageOfThemComesBack(Then[ManyPresetsAndACaller, SearchQueryDefinitionsPayload]):
    """크기를 지정하지 않은 검색은 한 페이지 분량만 응답하고, 다음 페이지가 있다고 알린다."""

    @override
    def says(self) -> str:
        return "한 페이지만 반환되고 다음 페이지가 있다고 응답한다"

    @override
    def look(
        self, laid: ManyPresetsAndACaller, answered: Answered[SearchQueryDefinitionsPayload]
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


def node_of(seeded: PrometheusQueryPresetData) -> QueryDefinitionNode:
    """The node a read of this seeded preset has to answer, whole."""
    return QueryDefinitionNode(
        id=seeded.id,
        name=seeded.name,
        description=seeded.description,
        rank=seeded.rank,
        category_id=seeded.category_id,
        metric_name=seeded.metric_name,
        query_template=seeded.query_template,
        time_window=seeded.time_window,
        options=QueryDefinitionOptionsInfo(
            filter_labels=seeded.filter_labels, group_labels=seeded.group_labels
        ),
        created_at=seeded.created_at,
        updated_at=seeded.updated_at,
    )


@dataclass(frozen=True)
class TheBatchAnswersInOrder(Then[ManyPresetsAndACaller, list[PresetNodeAnswer]]):
    """요청한 순서대로 응답한다. 미리 만들어 둔 것은 노드 전체로, 마지막의 없는 id는 빈 항목으로."""

    @override
    def says(self) -> str:
        return "요청한 순서대로, 없는 id 자리는 비어서 반환된다"

    @override
    def look(
        self, laid: ManyPresetsAndACaller, answered: Answered[list[PresetNodeAnswer]]
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
                    SameAs[PresetNodeAnswer](
                        node_of(wanted), f"{at + 1}번째로 요청한 id의 프리셋 전체"
                    ),
                )
            )
        seen.append(Same(f"[{len(laid.laid)}]", answer[-1], None))
        return seen


@dataclass(frozen=True)
class NothingIsAnswered(Then[Any, list[PresetNodeAnswer]]):
    """빈 목록에는 빈 응답이다."""

    @override
    def says(self) -> str:
        return "빈 응답이 반환된다"

    @override
    def look(self, laid: Any, answered: Answered[list[PresetNodeAnswer]]) -> list[Verdict]:
        answer = answered.response
        if answer is None:
            return [Refused(UserNotFound, answered.raised)]
        return [Same("answer", answer, [])]


@dataclass(frozen=True)
class TheQueryAnswered(Then[Any, QueryDefinitionResultInfo]):
    """모의 서버가 응답한 결과가 그대로 담겨 반환된다. 샘플의 값이 모의 서버가 받은 질의이므로,
    무엇이 Prometheus에 전달됐는지를 여기서 확인한다."""

    query: str
    result_type: str = INSTANT

    @override
    def says(self) -> str:
        return "모의 서버가 받은 질의를 담은 결과가 반환된다"

    @override
    def look(self, laid: Any, answered: Answered[QueryDefinitionResultInfo]) -> list[Verdict]:
        result = answered.response
        if result is None:
            return [Refused(PrometheusQueryPresetNotFound, answered.raised)]
        return [
            Same("status", result.status, "success"),
            Same("result_type", result.result_type, self.result_type),
            Same(
                "result",
                [
                    (
                        [(label.key, label.value) for label in one.metric],
                        [(sample.timestamp, sample.value) for sample in one.values],
                    )
                    for one in result.result
                ],
                [([], [(ANSWERED_AT, self.query)])],
            ),
        ]


@dataclass(frozen=True)
class TheRemovedOneIsNamed(Then[APresetAndACaller, DeleteQueryDefinitionPayload]):
    """삭제한 프리셋이 무엇인지 응답한다."""

    @override
    def says(self) -> str:
        return "삭제한 프리셋을 응답한다"

    @override
    def look(
        self, laid: APresetAndACaller, answered: Answered[DeleteQueryDefinitionPayload]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        return [Held("id", payload.id, SameAs[UUID](laid.preset.id, "미리 만들어 둔 프리셋"))]
