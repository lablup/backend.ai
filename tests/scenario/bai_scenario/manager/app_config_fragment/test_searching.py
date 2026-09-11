"""설정 조각 검색 — 한 스코프 검색과 전체 검색이 서로 다른 검사로 막는다.

한 스코프 검색은 지정한 소유자의 스코프에 부여된 읽기 권한을 검사하고, 공개 스코프에는 보호할
스코프가 없어 인증만으로 응답한다. 전체 검색은 전역 역할이 있어야 한다.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

import pytest
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.app_config_fragment import (
    EveryAnsweringFragmentIsFound,
    FragmentsLaidAcross,
    ManyFragmentsAndACaller,
    OnlyOneKindsFragmentsAreFound,
    OnlyTheNamedFragmentIsFound,
    TenFragmentsComeWithANextPage,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario
from bai_scenario.seeds.app_config.allow_list import SCOPE_NAMES

from ai.backend.common.data.app_config.types import AppConfigScopeType
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.common.dto.manager.v2.app_config_fragment.request import (
    AdminSearchAppConfigFragmentInput,
    AppConfigFragmentFilter,
    AppConfigFragmentScope,
    ScopedSearchAppConfigFragmentInput,
)
from ai.backend.common.dto.manager.v2.app_config_fragment.response import (
    SearchAppConfigFragmentPayload,
)
from ai.backend.common.dto.manager.v2.app_config_fragment.types import AppConfigScopeTypeFilter
from ai.backend.common.dto.manager.v2.rbac.types import UUIDScope
from ai.backend.manager.api.adapters.app_config_fragment.adapter import AppConfigFragmentAdapter
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.errors.resource import DomainNotFound
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Refused,
    Same,
    Scenario,
    Then,
    Verdict,
    When,
)

type Searched = SearchAppConfigFragmentPayload
type SearchingStep = Scenario[
    SeedingSession, ManyFragmentsAndACaller, AppConfigFragmentAdapter, Searched
]


@dataclass(frozen=True)
class SearchingTheScope(When[ManyFragmentsAndACaller, AppConfigFragmentAdapter, Searched]):
    """미리 만들어 둔 스코프 하나를 지정해 검색한다. 이름 필터를 걸 수도 있다."""

    by_name: bool = False

    @override
    def operation(self) -> str:
        return "scoped_search"

    @override
    def describe(self, laid: ManyFragmentsAndACaller) -> str:
        how = f"{laid.named} 이름 필터로" if self.by_name else "필터 없이"
        return f"{laid.caller.username}이 {SCOPE_NAMES[laid.scope_type]} 스코프를 지정해 {how} 조회"

    @override
    async def call(
        self, adapter: AppConfigFragmentAdapter, laid: ManyFragmentsAndACaller
    ) -> Searched:
        filter_ = (
            AppConfigFragmentFilter(config_name=StringFilter(equals=laid.named))
            if self.by_name
            else None
        )
        if laid.scope_type == AppConfigScopeType.PUBLIC:
            scope = AppConfigFragmentScope(public=True)
        elif laid.scope_id is None:
            raise LookupError("this row lays no owner to name")
        elif laid.scope_type == AppConfigScopeType.USER:
            scope = AppConfigFragmentScope(user=[UUIDScope(value=laid.scope_id)])
        else:
            scope = AppConfigFragmentScope(domain=[UUIDScope(value=laid.scope_id)])
        with ActingAs(laid.caller):
            return await adapter.scoped_search(
                ScopedSearchAppConfigFragmentInput(scope=scope, filter=filter_)
            )


@dataclass(frozen=True)
class SearchingTwoScopes(When[ManyFragmentsAndACaller, AppConfigFragmentAdapter, Searched]):
    """자기 도메인과 자기 자신을 함께 지정해 검색한다."""

    @override
    def operation(self) -> str:
        return "scoped_search"

    @override
    def describe(self, laid: ManyFragmentsAndACaller) -> str:
        return f"{laid.caller.username}이 도메인과 사용자를 함께 지정해 조회"

    @override
    async def call(
        self, adapter: AppConfigFragmentAdapter, laid: ManyFragmentsAndACaller
    ) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.scoped_search(
                ScopedSearchAppConfigFragmentInput(
                    scope=AppConfigFragmentScope(
                        domain=[UUIDScope(value=laid.domain.id)],
                        user=[UUIDScope(value=laid.caller.id)],
                    )
                )
            )


@dataclass(frozen=True)
class SearchingEverything(When[ManyFragmentsAndACaller, AppConfigFragmentAdapter, Searched]):
    """스코프 없이 전체를 검색한다. 종류나 이름 필터를 걸 수도 있다."""

    kind: AppConfigScopeType | None = None
    by_name: bool = False

    @override
    def operation(self) -> str:
        return "admin_search"

    @override
    def describe(self, laid: ManyFragmentsAndACaller) -> str:
        if self.kind is not None:
            return f"{laid.caller.username}이 {SCOPE_NAMES[self.kind]} 종류 필터로 전체 조회"
        if self.by_name:
            return f"{laid.caller.username}이 {laid.named} 이름 필터로 전체 조회"
        return f"{laid.caller.username}이 필터 없이 전체 조회"

    @override
    async def call(
        self, adapter: AppConfigFragmentAdapter, laid: ManyFragmentsAndACaller
    ) -> Searched:
        filter_ = None
        if self.kind is not None:
            filter_ = AppConfigFragmentFilter(scope_type=AppConfigScopeTypeFilter(equals=self.kind))
        elif self.by_name:
            filter_ = AppConfigFragmentFilter(config_name=StringFilter(equals=laid.named))
        with ActingAs(laid.caller):
            return await adapter.admin_search(AdminSearchAppConfigFragmentInput(filter=filter_))


@dataclass(frozen=True)
class SearchingAnotherUser(When[ManyFragmentsAndACaller, AppConfigFragmentAdapter, Searched]):
    """다른 사용자의 스코프를 지정해 검색한다. 그 사용자는 조각을 하나 갖고 있다."""

    @override
    def operation(self) -> str:
        return "scoped_search"

    @override
    def describe(self, laid: ManyFragmentsAndACaller) -> str:
        return f"{laid.caller.username}이 다른 사용자를 지정해 조회"

    @override
    async def call(
        self, adapter: AppConfigFragmentAdapter, laid: ManyFragmentsAndACaller
    ) -> Searched:
        if laid.other_id is None:
            raise LookupError("this row lays no other user to name")
        with ActingAs(laid.caller):
            return await adapter.scoped_search(
                ScopedSearchAppConfigFragmentInput(
                    scope=AppConfigFragmentScope(user=[UUIDScope(value=laid.other_id)])
                )
            )


@dataclass(frozen=True)
class EveryFragmentIsCounted(Then[ManyFragmentsAndACaller, Searched]):
    """미리 만들어 둔 조각이 스코프를 가리지 않고 모두 집계된다."""

    count: int

    @override
    def says(self) -> str:
        return "스코프를 가리지 않고 미리 만들어 둔 조각이 모두 집계된다"

    @override
    def look(self, laid: ManyFragmentsAndACaller, answered: Answered[Searched]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(InsufficientPrivilege, answered.raised)]
        return [
            Same("items", len(payload.items), self.count),
            Same("total_count", payload.total_count, self.count),
            Same("has_next_page", payload.has_next_page, False),
            Same("has_previous_page", payload.has_previous_page, False),
        ]


@dataclass(frozen=True)
class TheGrantedUserCountsTheirOwn(
    Scenario[SeedingSession, ManyFragmentsAndACaller, AppConfigFragmentAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "searching-my-own-scope-counts-only-my-fragments"

    @override
    def describe(self) -> str:
        return (
            "자기 조각 둘과 다른 사용자의 조각 하나가 있고 자기 스코프에 읽기 권한을 받은 "
            "사용자가 자기 스코프를 검색하면, 자기 조각 둘만 집계된다"
        )

    @override
    def given(self) -> Given[SeedingSession, ManyFragmentsAndACaller]:
        return FragmentsLaidAcross(mine=2, anothers=1, granted=(Permission.READ,))

    @override
    def when(self) -> When[ManyFragmentsAndACaller, AppConfigFragmentAdapter, Searched]:
        return SearchingTheScope()

    @override
    def then(self) -> Then[ManyFragmentsAndACaller, Searched]:
        return EveryAnsweringFragmentIsFound()


@dataclass(frozen=True)
class FilteringByNameKeepsOne(
    Scenario[SeedingSession, ManyFragmentsAndACaller, AppConfigFragmentAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "filtering-a-scope-by-name-keeps-only-that-fragment"

    @override
    def describe(self) -> str:
        return "자기 조각 둘이 있고 읽기 권한을 받은 사용자가 이름 필터로 검색하면, 그 이름의 조각만 반환된다"

    @override
    def given(self) -> Given[SeedingSession, ManyFragmentsAndACaller]:
        return FragmentsLaidAcross(mine=2, granted=(Permission.READ,))

    @override
    def when(self) -> When[ManyFragmentsAndACaller, AppConfigFragmentAdapter, Searched]:
        return SearchingTheScope(by_name=True)

    @override
    def then(self) -> Then[ManyFragmentsAndACaller, Searched]:
        return OnlyTheNamedFragmentIsFound()


@dataclass(frozen=True)
class NoPageSizeMeansTen(
    Scenario[SeedingSession, ManyFragmentsAndACaller, AppConfigFragmentAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "leaving-the-page-size-out-answers-ten-with-a-next-page"

    @override
    def describe(self) -> str:
        return "자기 조각 11개가 있고 읽기 권한을 받은 사용자가 크기 없이 검색하면, 10건까지 반환되고 다음 페이지가 있다고 응답한다"

    @override
    def given(self) -> Given[SeedingSession, ManyFragmentsAndACaller]:
        return FragmentsLaidAcross(mine=11, granted=(Permission.READ,))

    @override
    def when(self) -> When[ManyFragmentsAndACaller, AppConfigFragmentAdapter, Searched]:
        return SearchingTheScope()

    @override
    def then(self) -> Then[ManyFragmentsAndACaller, Searched]:
        return TenFragmentsComeWithANextPage()


@dataclass(frozen=True)
class AnyoneSignedInSearchesThePublic(
    Scenario[SeedingSession, ManyFragmentsAndACaller, AppConfigFragmentAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "anyone-signed-in-searches-the-public-scope"

    @override
    def describe(self) -> str:
        return (
            "공개 조각 둘이 있고 아무 권한도 없는 사용자가 공개 스코프를 지정해 검색하면, 둘 다 "
            "집계된다. 공개 조각에는 보호할 스코프가 없다"
        )

    @override
    def given(self) -> Given[SeedingSession, ManyFragmentsAndACaller]:
        return FragmentsLaidAcross(publics=2, answers=AppConfigScopeType.PUBLIC)

    @override
    def when(self) -> When[ManyFragmentsAndACaller, AppConfigFragmentAdapter, Searched]:
        return SearchingTheScope()

    @override
    def then(self) -> Then[ManyFragmentsAndACaller, Searched]:
        return EveryAnsweringFragmentIsFound()


@dataclass(frozen=True)
class TwoScopesAtOnceAreRefused(
    Scenario[SeedingSession, ManyFragmentsAndACaller, AppConfigFragmentAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "naming-two-scopes-at-once-is-refused-as-bad-input"

    @override
    def describe(self) -> str:
        return (
            "읽기 권한을 받은 사용자가 도메인과 사용자를 함께 지정해 검색하면, 잘못된 입력으로 "
            "거부된다. 이 검색은 한 스코프에서만 실행된다"
        )

    @override
    def given(self) -> Given[SeedingSession, ManyFragmentsAndACaller]:
        return FragmentsLaidAcross(mine=1, granted=(Permission.READ,))

    @override
    def when(self) -> When[ManyFragmentsAndACaller, AppConfigFragmentAdapter, Searched]:
        return SearchingTwoScopes()

    @override
    def then(self) -> Then[ManyFragmentsAndACaller, Searched]:
        return TheCallIsRefused(InvalidAPIParameters)


@dataclass(frozen=True)
class AnotherUsersScopeIsRefused(
    Scenario[SeedingSession, ManyFragmentsAndACaller, AppConfigFragmentAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-read-on-their-own-scope-may-not-search-another-users"

    @override
    def describe(self) -> str:
        return "자기 스코프에만 읽기 권한을 받은 사용자가 다른 사용자를 지정해 검색하면, 권한 부족으로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, ManyFragmentsAndACaller]:
        return FragmentsLaidAcross(mine=1, anothers=1, answers=None, granted=(Permission.READ,))

    @override
    def when(self) -> When[ManyFragmentsAndACaller, AppConfigFragmentAdapter, Searched]:
        return SearchingAnotherUser()

    @override
    def then(self) -> Then[ManyFragmentsAndACaller, Searched]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AMissingDomainIsNotFoundForASuperadmin(
    Scenario[SeedingSession, ManyFragmentsAndACaller, AppConfigFragmentAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-domain-nothing-answers-to-is-not-found-for-a-superadmin"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 어느 도메인도 아닌 id를 지정해 검색하면, 대상을 찾을 수 없다는 이유로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, ManyFragmentsAndACaller]:
        return FragmentsLaidAcross(
            answers=AppConfigScopeType.DOMAIN, missing_domain=True, role=UserRole.SUPERADMIN
        )

    @override
    def when(self) -> When[ManyFragmentsAndACaller, AppConfigFragmentAdapter, Searched]:
        return SearchingTheScope()

    @override
    def then(self) -> Then[ManyFragmentsAndACaller, Searched]:
        return TheCallIsRefused(DomainNotFound)


@dataclass(frozen=True)
class TheSuperadminCountsEveryOne(
    Scenario[SeedingSession, ManyFragmentsAndACaller, AppConfigFragmentAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-counts-every-fragment-across-scopes"

    @override
    def describe(self) -> str:
        return "공개·도메인·사용자 스코프에 조각 넷이 있고 슈퍼관리자가 전체를 검색하면, 넷 다 집계된다. 전체 검색은 전역 역할로 보호된다"

    @override
    def given(self) -> Given[SeedingSession, ManyFragmentsAndACaller]:
        return FragmentsLaidAcross(
            mine=2, domains=1, publics=1, answers=None, role=UserRole.SUPERADMIN
        )

    @override
    def when(self) -> When[ManyFragmentsAndACaller, AppConfigFragmentAdapter, Searched]:
        return SearchingEverything()

    @override
    def then(self) -> Then[ManyFragmentsAndACaller, Searched]:
        return EveryFragmentIsCounted(count=4)


@dataclass(frozen=True)
class FilteringByKindKeepsThatKind(
    Scenario[SeedingSession, ManyFragmentsAndACaller, AppConfigFragmentAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "filtering-everything-by-scope-kind-keeps-only-that-kinds-fragments"

    @override
    def describe(self) -> str:
        return "세 종류에 조각이 하나씩 있고 슈퍼관리자가 사용자 종류 필터로 검색하면, 사용자 조각만 반환된다"

    @override
    def given(self) -> Given[SeedingSession, ManyFragmentsAndACaller]:
        return FragmentsLaidAcross(
            mine=1, domains=1, publics=1, answers=None, role=UserRole.SUPERADMIN
        )

    @override
    def when(self) -> When[ManyFragmentsAndACaller, AppConfigFragmentAdapter, Searched]:
        return SearchingEverything(kind=AppConfigScopeType.USER)

    @override
    def then(self) -> Then[ManyFragmentsAndACaller, Searched]:
        return OnlyOneKindsFragmentsAreFound(kind=AppConfigScopeType.USER, count=1)


@dataclass(frozen=True)
class FilteringEverythingByNameKeepsOne(
    Scenario[SeedingSession, ManyFragmentsAndACaller, AppConfigFragmentAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "filtering-everything-by-name-keeps-only-that-fragment"

    @override
    def describe(self) -> str:
        return "이름이 다른 조각 여럿이 있고 슈퍼관리자가 이름 필터로 검색하면, 그 이름의 조각만 반환된다"

    @override
    def given(self) -> Given[SeedingSession, ManyFragmentsAndACaller]:
        return FragmentsLaidAcross(mine=2, publics=1, answers=None, role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyFragmentsAndACaller, AppConfigFragmentAdapter, Searched]:
        return SearchingEverything(by_name=True)

    @override
    def then(self) -> Then[ManyFragmentsAndACaller, Searched]:
        return OnlyTheNamedFragmentIsFound()


@dataclass(frozen=True)
class AGrantDoesNotOpenTheGlobalDoor(
    Scenario[SeedingSession, ManyFragmentsAndACaller, AppConfigFragmentAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-read-may-not-search-every-fragment"

    @override
    def describe(self) -> str:
        return (
            "자기 도메인 스코프에 읽기 권한을 받았지만 슈퍼관리자가 아닌 사용자가 전체를 검색하면, "
            "역할 부족으로 거부된다. 한 스코프를 검색하는 경로와 전체를 검색하는 경로가 다르다"
        )

    @override
    def given(self) -> Given[SeedingSession, ManyFragmentsAndACaller]:
        return FragmentsLaidAcross(
            domains=1, answers=AppConfigScopeType.DOMAIN, granted=(Permission.READ,)
        )

    @override
    def when(self) -> When[ManyFragmentsAndACaller, AppConfigFragmentAdapter, Searched]:
        return SearchingEverything()

    @override
    def then(self) -> Then[ManyFragmentsAndACaller, Searched]:
        return TheCallIsRefused(InsufficientPrivilege)


SCOPED_SCENARIOS: list[SearchingStep] = [
    TheGrantedUserCountsTheirOwn(),
    FilteringByNameKeepsOne(),
    NoPageSizeMeansTen(),
    AnyoneSignedInSearchesThePublic(),
    TwoScopesAtOnceAreRefused(),
    AnotherUsersScopeIsRefused(),
    AMissingDomainIsNotFoundForASuperadmin(),
]

GLOBAL_SCENARIOS: list[SearchingStep] = [
    TheSuperadminCountsEveryOne(),
    FilteringByKindKeepsThatKind(),
    FilteringEverythingByNameKeepsOne(),
    AGrantDoesNotOpenTheGlobalDoor(),
]


@pytest.mark.parametrize("scenario", SCOPED_SCENARIOS, ids=lambda s: s.summary())
async def test_searching_a_scope(
    scenario: SearchingStep, adapter: AppConfigFragmentAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)


@pytest.mark.parametrize("scenario", GLOBAL_SCENARIOS, ids=lambda s: s.summary())
async def test_searching_everything(
    scenario: SearchingStep, adapter: AppConfigFragmentAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
