"""Searching domains: what the filters narrow, and who may ask."""

from __future__ import annotations

import pytest
from bai_kit.manager.personas import DOMAIN_ADMIN, MEMBER
from bai_kit.manager.typed_runner import TypedRunner
from bai_kit.manager.wiring.domain import (
    DomainScenario,
    admin_search,
    already_there,
)

from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.common.dto.manager.v2.domain.request import (
    AdminSearchDomainsInput,
    DomainFilter,
)
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.testutils.typed_scenario import (
    TypedScenario,
    at,
    every,
)

SCENARIOS: list[DomainScenario] = [
    TypedScenario.ok(
        "an-untouched-world-answers-with-its-one-domain",
        when=admin_search(AdminSearchDomainsInput()),
        then=at(lambda p: p.total_count, 1),
    ),
    TypedScenario.ok(
        "a-name-filter-narrows-the-answer-to-the-domain-it-names",
        given=[already_there("alpha"), already_there("beta")],
        when=admin_search(
            AdminSearchDomainsInput(filter=DomainFilter(name=StringFilter(equals="alpha")))
        ),
        then=every(lambda p: p.items, at(lambda node: node.basic_info.name, "alpha")),
    ),
    TypedScenario.ok(
        "an-active-filter-leaves-out-what-was-retired",
        given=[already_there("retired")],
        when=admin_search(AdminSearchDomainsInput(filter=DomainFilter(is_active=True))),
        then=every(lambda p: p.items, at(lambda node: node.lifecycle.is_active, True)),
    ),
    TypedScenario.error(
        "the-domain-admin-may-not-search-every-domain",
        actor=DOMAIN_ADMIN,
        when=admin_search(AdminSearchDomainsInput()),
        then=InsufficientPrivilege,
    ),
    TypedScenario.error(
        "a-member-may-not-search-every-domain",
        actor=MEMBER,
        when=admin_search(AdminSearchDomainsInput()),
        then=InsufficientPrivilege,
    ),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.id)
async def test_searching(scenario: DomainScenario, run: TypedRunner) -> None:
    await run(scenario)
