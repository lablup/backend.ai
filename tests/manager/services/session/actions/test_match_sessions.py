from typing import cast
from unittest.mock import AsyncMock

import pytest

from ai.backend.common.types import AccessKey
from ai.backend.manager.services.session.actions.match_sessions import (
    MatchSessionsAction,
    MatchSessionsActionResult,
)
from ai.backend.manager.services.session.processors import SessionProcessors

from ...test_utils import TestScenario
from ..fixtures import (
    KERNEL_FIXTURE_DICT,
    SESSION_FIXTURE_DATA,
    SESSION_FIXTURE_DICT,
)


@pytest.fixture
def mock_match_sessions_rpc(mocker, mock_agent_response_result):
    mock = mocker.patch(
        "ai.backend.manager.services.session.service.SessionService._match_sessions",
        new_callable=AsyncMock,
    )
    mock.return_value = mock_agent_response_result
    return mock


MATCH_SESSIONS_MOCK = {
    "matches": [
        {"session_id": "session_123", "score": 0.95},
        {"session_id": "session_456", "score": 0.87},
    ]
}


@pytest.mark.parametrize(
    ("test_scenario", "mock_agent_response_result"),
    [
        (
            TestScenario.success(
                "Match sessions",
                MatchSessionsAction(
                    id_or_name_prefix=cast(str, SESSION_FIXTURE_DATA.name),
                    owner_access_key=cast(AccessKey, SESSION_FIXTURE_DATA.access_key),
                ),
                MatchSessionsActionResult(
                    result=MATCH_SESSIONS_MOCK,
                ),
            ),
            MATCH_SESSIONS_MOCK,
        ),
    ],
)
@pytest.mark.parametrize(
    "extra_fixtures",
    [
        {
            "sessions": [SESSION_FIXTURE_DICT],
            "kernels": [KERNEL_FIXTURE_DICT],
        }
    ],
)
async def test_match_sessions(
    mock_match_sessions_rpc,
    processors: SessionProcessors,
    test_scenario: TestScenario[MatchSessionsAction, MatchSessionsActionResult],
):
    await test_scenario.test(processors.match_sessions.wait_for_complete)
