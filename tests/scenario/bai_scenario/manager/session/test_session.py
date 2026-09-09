"""What the session adapter answers for a read, said as a request, an actor, and an answer.

Only the read half. What a session write needs is written down in the wiring, which
names the ten dependencies a read never reaches.
"""

from __future__ import annotations

import pytest
from bai_scenario.infra.personas import DOMAIN_ADMIN, MEMBER, OTHER_MEMBER
from bai_scenario.runner.runner import ScenarioRunner
from bai_scenario.seeds.seeding import (
    DOMAIN_ADMIN_PRESET,
    USER_PRESET,
    holds,
    on_the_domain,
    on_their_own_scope,
)

from ai.backend.common.dto.manager.v2.session.request import AdminSearchSessionsInput
from ai.backend.manager.api.adapters.session.adapter import SessionAdapter
from ai.backend.manager.config.unified import ManagerUnifiedConfig
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.testutils.typed_scenario import (
    TypedScenario,
    at,
    call,
)

type SessionScenario = TypedScenario[SessionAdapter, ManagerUnifiedConfig]

# The premise that decides the answers below: CRUD over the actor's own sessions.
THEIR_OWN_USER_ROLE = holds(USER_PRESET, on_their_own_scope())

SCENARIOS: list[SessionScenario] = [
    TypedScenario.ok(
        "an-untouched-world-holds-no-sessions",
        when=call(SessionAdapter.admin_search, AdminSearchSessionsInput()),
        then=at(lambda p: p.total_count, 0),
    ),
    TypedScenario.error(
        "a-member-granted-nothing-may-not-search-sessions",
        actor=MEMBER,
        when=call(SessionAdapter.admin_search, AdminSearchSessionsInput()),
        then=NotEnoughPermission,
    ),
    TypedScenario.ok(
        "a-member-lists-their-own-sessions-and-has-none",
        actor=MEMBER,
        holding=[THEIR_OWN_USER_ROLE],
        when=call(SessionAdapter.my_search, AdminSearchSessionsInput()),
        then=at(lambda p: p.total_count, 0),
    ),
    TypedScenario.ok(
        # Unlike a domain, whose search sits behind the superadmin role gate, a session
        # search is scope-gated. The member's own user preset grants session read on
        # their own scope, so the search runs and answers with what that scope holds.
        "a-member-may-search-sessions-because-their-own-scope-grants-it",
        actor=MEMBER,
        holding=[THEIR_OWN_USER_ROLE],
        when=call(SessionAdapter.admin_search, AdminSearchSessionsInput()),
        then=at(lambda p: p.total_count, 0),
    ),
    TypedScenario.ok(
        "a-member-outside-every-project-may-still-search-their-own-scope",
        actor=OTHER_MEMBER,
        holding=[THEIR_OWN_USER_ROLE],
        when=call(SessionAdapter.admin_search, AdminSearchSessionsInput()),
        then=at(lambda p: p.total_count, 0),
    ),
    TypedScenario.error(
        # The domain admin preset covers users, not sessions, so even holding it the
        # same request a plain member may make is refused. An admin role is not the
        # same thing as the permission the request needs.
        "the-domain-admin-role-does-not-reach-sessions",
        actor=DOMAIN_ADMIN,
        holding=[holds(DOMAIN_ADMIN_PRESET, on_the_domain())],
        when=call(SessionAdapter.admin_search, AdminSearchSessionsInput()),
        then=NotEnoughPermission,
    ),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary)
async def test_session(scenario: SessionScenario, run: ScenarioRunner) -> None:
    await run(scenario)
