"""Searching domains: what the filters narrow, and who may ask."""

from __future__ import annotations

import pytest
from bai_scenario.components.domain import DomainScenario, seed_someone_of
from bai_scenario.runner.runner import ScenarioRunner
from bai_scenario.seeds.domain.domain import seed_domain
from bai_scenario.seeds.seeder import Seeder

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.common.dto.manager.v2.domain.request import (
    AdminSearchDomainsInput,
    DomainFilter,
)
from ai.backend.manager.api.adapters.domain.adapter import DomainAdapter
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.testutils.typed_scenario import TypedScenario, at, call, every


def the_count_is_what_was_laid(seed: Seeder) -> DomainScenario:
    home = seed.creating(seed_domain(name_hint="home"))
    others = [seed.creating(seed_domain(name_hint="other")) for _ in range(3)]
    superadmin = seed_someone_of(seed, home, role=UserRole.SUPERADMIN)
    return TypedScenario.ok(
        "the-answer-counts-every-domain-the-scenario-laid",
        description=("이 시나리오가 심은 도메인이 넷일 때, 필터 없는 조회는 그 넷을 모두 센다"),
        actor=superadmin,
        given=seed.situation(),
        then=at(lambda p: p.total_count, 1 + len(others)),
        when=call(DomainAdapter.admin_search, AdminSearchDomainsInput()),
    )


def a_name_filter_narrows(seed: Seeder) -> DomainScenario:
    home = seed.creating(seed_domain(name_hint="home"))
    wanted = seed.creating(seed_domain(name_hint="wanted"))
    seed.creating(seed_domain(name_hint="other"))
    superadmin = seed_someone_of(seed, home, role=UserRole.SUPERADMIN)
    return TypedScenario.ok(
        "a-name-filter-narrows-the-answer-to-the-domain-it-names",
        description=(
            "도메인 여럿 중 하나의 이름으로 걸러 조회하면, 답에는 그 이름의 도메인만 남는다"
        ),
        actor=superadmin,
        given=seed.situation(),
        when=call(
            DomainAdapter.admin_search,
            AdminSearchDomainsInput(filter=DomainFilter(name=StringFilter(equals=wanted.name))),
        ),
        then=every(lambda p: p.items, at(lambda node: node.basic_info.name, wanted.name)),
    )


def ungranted_user_is_refused(seed: Seeder) -> DomainScenario:
    home = seed.creating(seed_domain(name_hint="home"))
    someone = seed_someone_of(seed, home)
    return TypedScenario.error(
        "a-user-who-is-not-the-superadmin-may-not-search-every-domain",
        description=("슈퍼관리자가 아닌 사용자가 전체 도메인 조회를 요청하면 역할로 막힌다"),
        actor=someone,
        given=seed.situation(),
        when=call(DomainAdapter.admin_search, AdminSearchDomainsInput()),
        then=InsufficientPrivilege,
    )


BUILDERS = (the_count_is_what_was_laid, a_name_filter_narrows, ungranted_user_is_refused)
SCENARIOS: list[DomainScenario] = [build(Seeder()) for build in BUILDERS]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary)
async def test_searching(scenario: DomainScenario, run: ScenarioRunner) -> None:
    await run(scenario)
