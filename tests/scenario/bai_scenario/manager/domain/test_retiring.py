"""Retiring, restoring and purging a domain."""

from __future__ import annotations

import pytest
from bai_scenario.components.domain import (
    ADomainIsThere,
    DomainScenario,
)
from bai_scenario.infra.personas import MEMBER, OTHER_MEMBER
from bai_scenario.runner.runner import ScenarioRunner

from ai.backend.common.dto.manager.v2.domain.request import (
    DeleteDomainInput,
    PurgeDomainInput,
    RestoreDomainInput,
)
from ai.backend.manager.api.adapters.domain.adapter import DomainAdapter
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.errors.permission import NotEnoughPermission
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
        "superadmin-retires-a-domain",
        given=situation(setup=A_DOMAIN),
        when=after(
            A_DOMAIN.domain,
            lambda row: call(DomainAdapter.admin_delete, DeleteDomainInput(name=row.name)),
        ),
        then=at(lambda p: p.deleted, True),
    ),
    TypedScenario.ok(
        "restoring-answers-that-it-restored",
        given=situation(setup=A_DOMAIN),
        when=after(
            A_DOMAIN.domain,
            lambda row: call(DomainAdapter.admin_restore, RestoreDomainInput(name=row.name)),
        ),
        then=at(lambda p: p.restored, True),
    ),
    TypedScenario.ok(
        "purging-a-domain-nothing-else-refers-to-succeeds",
        given=situation(setup=A_DOMAIN),
        when=after(
            A_DOMAIN.domain,
            lambda row: call(DomainAdapter.admin_purge, PurgeDomainInput(name=row.name)),
        ),
        then=at(lambda p: p.purged, True),
    ),
    TypedScenario.error(
        "retiring-a-name-nothing-answers-to-is-not-found",
        # The literal is the point here: nothing answers to it.
        when=call(DomainAdapter.admin_delete, DeleteDomainInput(name="no-such-domain")),
        then=EntityNotFoundError,
    ),
    TypedScenario.error(
        "a-member-may-not-retire-a-domain",
        actor=MEMBER,
        given=situation(setup=A_DOMAIN),
        when=after(
            A_DOMAIN.domain,
            lambda row: call(DomainAdapter.admin_delete, DeleteDomainInput(name=row.name)),
        ),
        then=NotEnoughPermission,
    ),
    TypedScenario.error(
        "a-member-outside-everything-may-not-purge-a-domain",
        actor=OTHER_MEMBER,
        given=situation(setup=A_DOMAIN),
        when=after(
            A_DOMAIN.domain,
            lambda row: call(DomainAdapter.admin_purge, PurgeDomainInput(name=row.name)),
        ),
        then=NotEnoughPermission,
    ),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary)
async def test_retiring(scenario: DomainScenario, run: ScenarioRunner) -> None:
    await run(scenario)
