"""Reading one domain by name, and who is allowed to."""

from __future__ import annotations

import pytest
from bai_scenario.components.domain import (
    ADomainIsThere,
    DomainScenario,
    enforcement_off,
    the_domain_admin_role,
)
from bai_scenario.infra.personas import DOMAIN_ADMIN, MEMBER
from bai_scenario.runner.runner import ScenarioRunner

from ai.backend.manager.api.adapters.domain.adapter import DomainAdapter
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.errors.repository import EntityNotFoundError
from ai.backend.testutils.typed_scenario import (
    TypedScenario,
    after,
    at,
    call,
    situation,
)

A_DOMAIN = ADomainIsThere()

SCENARIOS: list[DomainScenario] = [
    TypedScenario.ok(
        "superadmin-reads-a-domain-by-name",
        given=situation(setup=A_DOMAIN),
        when=after(A_DOMAIN.domain, lambda row: call(DomainAdapter.get, row.name)),
        then=at(lambda node: node.basic_info.description, A_DOMAIN.description),
    ),
    TypedScenario.error(
        "reading-a-name-nothing-answers-to-is-not-found",
        when=call(DomainAdapter.get, "no-such-domain"),
        then=EntityNotFoundError,
    ),
    TypedScenario.error(
        "the-domain-admin-holds-nothing-on-the-domain-entity-itself",
        actor=DOMAIN_ADMIN,
        holding=[the_domain_admin_role()],
        given=situation(setup=A_DOMAIN),
        when=after(A_DOMAIN.domain, lambda row: call(DomainAdapter.get, row.name)),
        then=NotEnoughPermission,
    ),
    TypedScenario.error(
        "a-member-may-not-read-a-domain",
        actor=MEMBER,
        given=situation(setup=A_DOMAIN),
        when=after(A_DOMAIN.domain, lambda row: call(DomainAdapter.get, row.name)),
        then=NotEnoughPermission,
    ),
    TypedScenario.ok(
        # Here the refusal does come from the permission graph, so turning enforcement
        # off lets the same request through. The contrast with creation is the point.
        "turning-enforcement-off-lets-a-member-read-a-domain",
        actor=MEMBER,
        given=enforcement_off(A_DOMAIN),
        when=after(A_DOMAIN.domain, lambda row: call(DomainAdapter.get, row.name)),
        then=at(lambda node: node.basic_info.name, A_DOMAIN.name),
    ),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary)
async def test_reading(scenario: DomainScenario, run: ScenarioRunner) -> None:
    await run(scenario)
