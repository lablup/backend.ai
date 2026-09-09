"""What the session adapter answers for a read, said as a request, an actor, and an answer.

Only the read half. What a session write needs is written down in the wiring, which
names the ten dependencies a read never reaches.
"""

from __future__ import annotations

from typing import Any

import pytest
from bai_kit.manager.config import base_config_dict
from bai_kit.manager.db import TemplateDatabase
from bai_kit.manager.monitors import ActionRecorder
from bai_kit.manager.personas import DOMAIN_ADMIN, MEMBER, OTHER_MEMBER
from bai_kit.manager.typed_runner import TypedRunner
from bai_kit.manager.wiring.session import my_sessions, search_sessions, session_wiring

from ai.backend.common.dto.manager.v2.session.request import AdminSearchSessionsInput
from ai.backend.manager.api.adapters.session.adapter import SessionAdapter
from ai.backend.manager.config.unified import ManagerUnifiedConfig
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.testutils.typed_scenario import TypedScenario, at

type SessionScenario = TypedScenario[SessionAdapter, ManagerUnifiedConfig]

SCENARIOS: list[SessionScenario] = [
    TypedScenario.ok(
        "an-untouched-world-holds-no-sessions",
        when=search_sessions(AdminSearchSessionsInput()),
        then=at(lambda p: p.total_count, 0),
    ),
    TypedScenario.ok(
        "a-member-lists-their-own-sessions-and-has-none",
        actor=MEMBER,
        when=my_sessions(AdminSearchSessionsInput()),
        then=at(lambda p: p.total_count, 0),
    ),
    TypedScenario.ok(
        # Unlike a domain, whose search sits behind the superadmin role gate, a session
        # search is scope-gated. The member's own user preset grants session read on
        # their own scope, so the search runs and answers with what that scope holds.
        "a-member-may-search-sessions-because-their-own-scope-grants-it",
        actor=MEMBER,
        when=search_sessions(AdminSearchSessionsInput()),
        then=at(lambda p: p.total_count, 0),
    ),
    TypedScenario.ok(
        "a-member-outside-every-project-may-still-search-their-own-scope",
        actor=OTHER_MEMBER,
        when=search_sessions(AdminSearchSessionsInput()),
        then=at(lambda p: p.total_count, 0),
    ),
    TypedScenario.error(
        # The domain admin preset covers users, not sessions, so the same request that
        # a plain member may make is refused here. Holding an admin role is not the
        # same as holding the permission the request needs.
        "the-domain-admin-holds-nothing-on-sessions-and-is-refused",
        actor=DOMAIN_ADMIN,
        when=search_sessions(AdminSearchSessionsInput()),
        then=NotEnoughPermission,
    ),
]


@pytest.fixture
def run(
    world_template: TemplateDatabase,
    test_db: str,
    engine: Any,
    recorder: ActionRecorder,
) -> TypedRunner:
    return TypedRunner(
        wiring=session_wiring,
        engine=engine,
        world=world_template.world,
        base_config=base_config_dict(world_template.addr, test_db, None),
        recorder=recorder,
    )


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.id)
async def test_session(scenario: SessionScenario, run: TypedRunner) -> None:
    await run(scenario)
