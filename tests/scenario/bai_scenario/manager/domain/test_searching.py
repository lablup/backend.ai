"""Searching domains: what the filters narrow, and who may ask."""

from __future__ import annotations

import pytest
from bai_scenario.components.domain import (
    ADomainIsThere,
    DomainScenario,
    SomeDomainsAreThere,
    TwoDomainsAreThere,
    the_domain_admin_role,
)
from bai_scenario.infra.personas import DOMAIN_ADMIN, MEMBER
from bai_scenario.runner.runner import ScenarioRunner

from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.common.dto.manager.v2.domain.request import (
    AdminSearchDomainsInput,
    DomainFilter,
)
from ai.backend.manager.api.adapters.domain.adapter import DomainAdapter
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.testutils.typed_scenario import (
    TypedScenario,
    at,
    call,
    every,
    situation,
)

ALPHA_AND_BETA = TwoDomainsAreThere("alpha", "beta")
A_RETIRED_DOMAIN = ADomainIsThere("retired")
THREE_MORE = SomeDomainsAreThere(3)

SCENARIOS: list[DomainScenario] = [
    TypedScenario.ok(
        "an-untouched-world-answers-with-its-one-domain",
        when=call(DomainAdapter.admin_search, AdminSearchDomainsInput()),
        then=at(lambda p: p.total_count, 1),
    ),
    TypedScenario.ok(
        "a-name-filter-narrows-the-answer-to-the-domain-it-names",
        given=situation(setup=ALPHA_AND_BETA),
        when=call(
            DomainAdapter.admin_search,
            AdminSearchDomainsInput(
                filter=DomainFilter(name=StringFilter(equals=ALPHA_AND_BETA.first_name))
            ),
        ),
        then=every(
            lambda p: p.items, at(lambda node: node.basic_info.name, ALPHA_AND_BETA.first_name)
        ),
    ),
    TypedScenario.ok(
        "an-active-filter-leaves-out-what-was-retired",
        given=situation(setup=A_RETIRED_DOMAIN),
        when=call(
            DomainAdapter.admin_search, AdminSearchDomainsInput(filter=DomainFilter(is_active=True))
        ),
        then=every(lambda p: p.items, at(lambda node: node.lifecycle.is_active, True)),
    ),
    TypedScenario.ok(
        # The count is what this row is about, so it is written once and the answer is
        # read against it rather than against a number copied by hand.
        "the-answer-counts-the-world-domain-and-everything-already-there",
        given=situation(setup=THREE_MORE),
        when=call(DomainAdapter.admin_search, AdminSearchDomainsInput()),
        then=at(lambda p: p.total_count, THREE_MORE.count + 1),
    ),
    TypedScenario.error(
        "the-domain-admin-may-not-search-every-domain",
        actor=DOMAIN_ADMIN,
        holding=[the_domain_admin_role()],
        when=call(DomainAdapter.admin_search, AdminSearchDomainsInput()),
        then=InsufficientPrivilege,
    ),
    TypedScenario.error(
        "a-member-may-not-search-every-domain",
        actor=MEMBER,
        when=call(DomainAdapter.admin_search, AdminSearchDomainsInput()),
        then=InsufficientPrivilege,
    ),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary)
async def test_searching(scenario: DomainScenario, run: ScenarioRunner) -> None:
    await run(scenario)
