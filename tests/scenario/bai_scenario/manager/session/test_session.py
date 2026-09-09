"""Session scenarios: the shape tried on a domain whose reads go through a service.

Only the read half is here. What a write needs is written down in the wiring, which
names the ten dependencies a read never reaches.
"""

from __future__ import annotations

import pytest
from bai_kit.manager.personas import MEMBER
from bai_kit.manager.wiring.session import session_wiring

from ai.backend.common.dto.manager.v2.session.request import AdminSearchSessionsInput
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.testutils.scenario import Runner, Scenario, has, length, scenario_id

WIRING = session_wiring

SCENARIOS = [
    Scenario.ok(
        "an-empty-world-holds-no-sessions",
        when=AdminSearchSessionsInput(),
        then=has(items=length(0), total_count=0),
    ),
    Scenario.error(
        # Unlike domain, whose search is behind the superadmin gate, a session search
        # is scope-gated: the member is refused on their own scope rather than by role.
        "member-is-refused-on-their-own-scope",
        actor=MEMBER,
        when=AdminSearchSessionsInput(),
        then=NotEnoughPermission,
    ),
]


@pytest.mark.parametrize("s", SCENARIOS, ids=scenario_id)
async def test_session(s: Scenario, run: Runner) -> None:
    await run(s)
