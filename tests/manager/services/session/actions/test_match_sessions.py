from typing import cast

import pytest

from ai.backend.common.types import AccessKey
from ai.backend.manager.services.session.actions.match_sessions import (
    MatchSessionsAction,
    MatchSessionsActionResult,
)
from ai.backend.manager.services.session.processors import SessionProcessors

from ...utils import ScenarioBase
from ..fixtures import (
    AGENT_FIXTURE_DICT,
    GROUP_FIXTURE_DATA,
    GROUP_USER_ASSOCIATION_DATA,
    KERNEL_FIXTURE_DICT,
    SESSION_FIXTURE_DATA,
    SESSION_FIXTURE_DICT,
    USER_FIXTURE_DATA,
)

MATCH_SESSIONS_MOCK = [
    {
        "id": str(SESSION_FIXTURE_DATA.id),
        "name": str(SESSION_FIXTURE_DATA.name),
        "status": "RUNNING",
    }
]


@pytest.mark.parametrize(
    ("test_scenario",),
    [
        (
            ScenarioBase.success(
                "Match sessions",
                MatchSessionsAction(
                    id_or_name_prefix=cast(str, SESSION_FIXTURE_DATA.name),
                    owner_access_key=cast(AccessKey, SESSION_FIXTURE_DATA.access_key),
                ),
                MatchSessionsActionResult(
                    result=MATCH_SESSIONS_MOCK,
                ),
            ),
        ),
    ],
)
@pytest.mark.parametrize(
    "extra_fixtures",
    [
        {
            "agents": [AGENT_FIXTURE_DICT],
            "sessions": [SESSION_FIXTURE_DICT],
            "kernels": [KERNEL_FIXTURE_DICT],
            "users": [USER_FIXTURE_DATA],
            "groups": [GROUP_FIXTURE_DATA],
            "association_groups_users": [GROUP_USER_ASSOCIATION_DATA],
        }
    ],
)
async def test_match_sessions(
    processors: SessionProcessors,
    test_scenario: ScenarioBase[MatchSessionsAction, MatchSessionsActionResult],
    session_repository,
):
    await test_scenario.test(processors.match_sessions.wait_for_complete)
