"""설정 조각 검색 — 한 스코프 검색과 전체 검색이 서로 다른 검사로 막는다.

한 스코프 검색은 지정한 소유자의 스코프에 부여된 읽기 권한을 검사하고, 공개 스코프에는 보호할
스코프가 없어 인증만으로 응답한다. 전체 검색은 슈퍼관리자인지 검사한다.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

import pytest

from ai.backend.common.data.app_config.types import AppConfigScopeType
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.app_config_fragment.request import (
    AdminSearchAppConfigFragmentInput,
    AppConfigFragmentScope,
    ScopedSearchAppConfigFragmentInput,
)
from ai.backend.common.dto.manager.v2.app_config_fragment.response import (
    SearchAppConfigFragmentPayload,
)
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
    Language,
    Refused,
    Same,
    Says,
    Scenario,
    Then,
    Verdict,
    When,
    in_language,
)
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.app_config_fragment import (
    EveryAnsweringFragmentIsFound,
    FragmentsLaidAcross,
    ManyFragmentsAndACaller,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario
from bai_scenario.seeds.app_config.allow_list import SCOPE_NAMES

type Searched = SearchAppConfigFragmentPayload
type SearchingStep = Scenario[
    TestSeedingSession, ManyFragmentsAndACaller, AppConfigFragmentAdapter, Searched
]


@dataclass(frozen=True)
class SearchingTheScope(When[ManyFragmentsAndACaller, AppConfigFragmentAdapter, Searched]):
    """미리 만들어 둔 스코프 하나를 지정해 검색한다."""

    @override
    def operation(self) -> str:
        return "scoped_search"

    @override
    def describe(self, laid: ManyFragmentsAndACaller) -> str:
        scope = SCOPE_NAMES[laid.scope_type]
        return Says(
            f"{laid.caller.username} 이 {scope} 스코프를 지정해 필터 없이 조회합니다",
            english=(
                f"{laid.caller.username} reads without a filter in the "
                f"{in_language(scope, Language.ENGLISH)} scope"
            ),
        )

    @override
    async def call(
        self, adapter: AppConfigFragmentAdapter, laid: ManyFragmentsAndACaller
    ) -> Searched:
        if laid.scope_type == AppConfigScopeType.PUBLIC:
            scope = AppConfigFragmentScope(public=True)
        elif laid.scope_id is None:
            raise LookupError("this row lays no owner to name")
        elif laid.scope_type == AppConfigScopeType.USER:
            scope = AppConfigFragmentScope(user=[UUIDScope(value=laid.scope_id)])
        else:
            scope = AppConfigFragmentScope(domain=[UUIDScope(value=laid.scope_id)])
        with ActingAs(laid.caller):
            return await adapter.scoped_search(ScopedSearchAppConfigFragmentInput(scope=scope))


@dataclass(frozen=True)
class SearchingTwoScopes(When[ManyFragmentsAndACaller, AppConfigFragmentAdapter, Searched]):
    """자기 도메인과 자기 자신을 함께 지정해 검색한다."""

    @override
    def operation(self) -> str:
        return "scoped_search"

    @override
    def describe(self, laid: ManyFragmentsAndACaller) -> str:
        return Says(
            f"{laid.caller.username} 이 도메인과 사용자를 함께 지정해 조회합니다",
            english=f"{laid.caller.username} reads by naming a domain and a user together",
        )

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
    """스코프 없이 전체를 검색한다."""

    @override
    def operation(self) -> str:
        return "admin_search"

    @override
    def describe(self, laid: ManyFragmentsAndACaller) -> str:
        return Says(
            f"{laid.caller.username} 이 필터 없이 전체를 조회합니다",
            english=f"{laid.caller.username} reads everything without a filter",
        )

    @override
    async def call(
        self, adapter: AppConfigFragmentAdapter, laid: ManyFragmentsAndACaller
    ) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.admin_search(AdminSearchAppConfigFragmentInput())


@dataclass(frozen=True)
class SearchingAnotherUser(When[ManyFragmentsAndACaller, AppConfigFragmentAdapter, Searched]):
    """다른 사용자의 스코프를 지정해 검색한다. 그 사용자는 조각을 하나 갖고 있다."""

    @override
    def operation(self) -> str:
        return "scoped_search"

    @override
    def describe(self, laid: ManyFragmentsAndACaller) -> str:
        return Says(
            f"{laid.caller.username} 이 다른 사용자를 지정해 조회합니다",
            english=f"{laid.caller.username} reads by naming another user",
        )

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
        return Says(
            "스코프를 가리지 않고 미리 저장한 조각이 모두 집계됩니다",
            english="every fragment made in advance is counted across scopes",
        )

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
    Scenario[TestSeedingSession, ManyFragmentsAndACaller, AppConfigFragmentAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "searching-my-own-scope-counts-only-my-fragments"

    @override
    def describe(self) -> str:
        return Says(
            "자기 조각 둘과 다른 사용자의 조각 하나가 있고 자기 스코프에 읽기 권한을 받은 "
            "사용자가 자기 스코프를 검색하면, 자기 조각 둘만 집계됩니다",
            english=(
                "when two own fragments and one fragment of another user exist and a user "
                "granted read permission on their own scope searches their own scope, only "
                "the two own fragments are counted"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyFragmentsAndACaller]:
        return FragmentsLaidAcross(mine=2, anothers=1, granted=(Permission.READ,))

    @override
    def when(self) -> When[ManyFragmentsAndACaller, AppConfigFragmentAdapter, Searched]:
        return SearchingTheScope()

    @override
    def then(self) -> Then[ManyFragmentsAndACaller, Searched]:
        return EveryAnsweringFragmentIsFound()


@dataclass(frozen=True)
class AnyoneSignedInSearchesThePublic(
    Scenario[TestSeedingSession, ManyFragmentsAndACaller, AppConfigFragmentAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "anyone-signed-in-searches-the-public-scope"

    @override
    def describe(self) -> str:
        return Says(
            "공개 조각 둘이 있고 아무 권한도 없는 사용자가 공개 스코프를 지정해 검색하면, 둘 다 "
            "집계됩니다. 공개 조각에는 보호할 스코프가 없습니다",
            english=(
                "when two public fragments exist and a user with no permission searches by "
                "naming the public scope, both are counted. A public fragment has no scope to "
                "protect"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyFragmentsAndACaller]:
        return FragmentsLaidAcross(publics=2, answers=AppConfigScopeType.PUBLIC)

    @override
    def when(self) -> When[ManyFragmentsAndACaller, AppConfigFragmentAdapter, Searched]:
        return SearchingTheScope()

    @override
    def then(self) -> Then[ManyFragmentsAndACaller, Searched]:
        return EveryAnsweringFragmentIsFound()


@dataclass(frozen=True)
class TwoScopesAtOnceAreRefused(
    Scenario[TestSeedingSession, ManyFragmentsAndACaller, AppConfigFragmentAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "naming-two-scopes-at-once-is-refused-as-bad-input"

    @override
    def describe(self) -> str:
        return Says(
            "읽기 권한을 받은 사용자가 도메인과 사용자를 함께 지정해 검색하면, 잘못된 입력으로 "
            "거부됩니다. 이 검색은 한 스코프에서만 실행됩니다",
            english=(
                "when a user granted read permission searches by naming a domain and a user "
                "together, it is rejected as bad input. This search runs in one scope only"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyFragmentsAndACaller]:
        return FragmentsLaidAcross(mine=1, granted=(Permission.READ,))

    @override
    def when(self) -> When[ManyFragmentsAndACaller, AppConfigFragmentAdapter, Searched]:
        return SearchingTwoScopes()

    @override
    def then(self) -> Then[ManyFragmentsAndACaller, Searched]:
        return TheCallIsRefused(InvalidAPIParameters)


@dataclass(frozen=True)
class AnotherUsersScopeIsRefused(
    Scenario[TestSeedingSession, ManyFragmentsAndACaller, AppConfigFragmentAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-read-on-their-own-scope-may-not-search-another-users"

    @override
    def describe(self) -> str:
        return Says(
            "자기 스코프에만 읽기 권한을 받은 사용자가 다른 사용자를 지정해 검색하면, "
            "권한 부족으로 거부됩니다",
            english=(
                "when a user granted read permission only on their own scope searches by "
                "naming another user, it is rejected for lack of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyFragmentsAndACaller]:
        return FragmentsLaidAcross(mine=1, anothers=1, answers=None, granted=(Permission.READ,))

    @override
    def when(self) -> When[ManyFragmentsAndACaller, AppConfigFragmentAdapter, Searched]:
        return SearchingAnotherUser()

    @override
    def then(self) -> Then[ManyFragmentsAndACaller, Searched]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AMissingDomainIsNotFoundForASuperadmin(
    Scenario[TestSeedingSession, ManyFragmentsAndACaller, AppConfigFragmentAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-domain-nothing-answers-to-is-not-found-for-a-superadmin"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 어느 도메인도 아닌 id 를 지정해 검색하면, 대상을 찾을 수 없다는 이유로 "
            "거부됩니다",
            english=(
                "when the superadmin searches by naming an id that belongs to no domain, it is "
                "rejected because no such target exists"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyFragmentsAndACaller]:
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
    Scenario[TestSeedingSession, ManyFragmentsAndACaller, AppConfigFragmentAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-counts-every-fragment-across-scopes"

    @override
    def describe(self) -> str:
        return Says(
            "공개, 도메인, 사용자 스코프에 조각 넷이 있고 superadmin 이 전체를 검색하면, 넷 다 "
            "집계됩니다. 전체 검색은 superadmin 인지 검사합니다",
            english=(
                "when four fragments exist across the public, domain and user scopes and the "
                "superadmin searches everything, all four are counted. The global search checks "
                "whether the caller is the superadmin"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyFragmentsAndACaller]:
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
class AGrantDoesNotOpenTheGlobalDoor(
    Scenario[TestSeedingSession, ManyFragmentsAndACaller, AppConfigFragmentAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-read-may-not-search-every-fragment"

    @override
    def describe(self) -> str:
        return Says(
            "자기 도메인 스코프에 읽기 권한을 받았지만 superadmin 이 아닌 사용자가 전체를 검색하면, "
            "역할 부족으로 거부됩니다. 한 스코프를 검색하는 경로와 전체를 검색하는 경로가 다릅니다",
            english=(
                "when a user granted read permission on their own domain scope but who is not "
                "the superadmin searches everything, it is rejected for lack of role. Searching "
                "one scope and searching everything take different paths"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyFragmentsAndACaller]:
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
    AnyoneSignedInSearchesThePublic(),
    TwoScopesAtOnceAreRefused(),
    AnotherUsersScopeIsRefused(),
    AMissingDomainIsNotFoundForASuperadmin(),
]

GLOBAL_SCENARIOS: list[SearchingStep] = [
    TheSuperadminCountsEveryOne(),
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
