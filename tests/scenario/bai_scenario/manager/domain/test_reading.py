"""Reading one domain by name, and who is allowed to."""

from __future__ import annotations

import pytest
from bai_kit.manager.personas import DOMAIN_ADMIN, MEMBER
from bai_kit.manager.typed_runner import TypedRunner
from bai_kit.manager.wiring.domain import (
    ENFORCEMENT_OFF,
    SEEDED_DESCRIPTION,
    DomainScenario,
    already_there,
    get_domain,
)

from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.errors.repository import EntityNotFoundError
from ai.backend.testutils.typed_scenario import (
    TypedScenario,
    at,
)

SCENARIOS: list[DomainScenario] = [
    TypedScenario.ok(
        "superadmin-reads-a-domain-by-name",
        given=[already_there("readable")],
        when=get_domain("readable"),
        then=at(lambda node: node.basic_info.description, SEEDED_DESCRIPTION),
    ),
    TypedScenario.error(
        "reading-a-name-nothing-answers-to-is-not-found",
        when=get_domain("no-such-domain"),
        then=EntityNotFoundError,
    ),
    TypedScenario.error(
        "the-domain-admin-holds-nothing-on-the-domain-entity-itself",
        actor=DOMAIN_ADMIN,
        given=[already_there("admin-cannot-read")],
        when=get_domain("admin-cannot-read"),
        then=NotEnoughPermission,
    ),
    TypedScenario.error(
        "a-member-may-not-read-a-domain",
        actor=MEMBER,
        given=[already_there("member-cannot-read")],
        when=get_domain("member-cannot-read"),
        then=NotEnoughPermission,
    ),
    TypedScenario.ok(
        # Here the refusal does come from the permission graph, so turning enforcement
        # off lets the same request through. The contrast with creation is the point.
        "turning-enforcement-off-lets-a-member-read-a-domain",
        actor=MEMBER,
        setup=ENFORCEMENT_OFF,
        given=[already_there("now-readable")],
        when=get_domain("now-readable"),
        then=at(lambda node: node.basic_info.name, "now-readable"),
    ),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.id)
async def test_reading(scenario: DomainScenario, run: TypedRunner) -> None:
    await run(scenario)
