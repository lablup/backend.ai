from typing import cast
from unittest.mock import AsyncMock

import pytest

from ai.backend.common.types import AccessKey
from ai.backend.manager.services.session.actions.restart_session import (
    RestartSessionAction,
    RestartSessionActionResult,
)
from ai.backend.manager.services.session.processors import SessionProcessors

from ...utils import TestScenario
from ..fixtures import (
    KERNEL_FIXTURE_DICT,
    SESSION_FIXTURE_DATA,
    SESSION_FIXTURE_DICT,
)


@pytest.fixture
def mock_restart_session_rpc(mocker, mock_agent_response_result):
    mocker.patch(
        "ai.backend.manager.registry.AgentRegistry.restart_session",
        new_callable=AsyncMock,
    )

    return mock_agent_response_result


@pytest.fixture
def mock_increment_session_usage_rpc(mocker, mock_agent_response_result):
    mocker.patch(
        "ai.backend.manager.registry.AgentRegistry.increment_session_usage",
        new_callable=AsyncMock,
    )

    return mock_agent_response_result


RESTART_SESSION_MOCK = None


@pytest.mark.parametrize(
    ("test_scenario", "mock_agent_response_result"),
    [
        (
            TestScenario.success(
                "Restart session",
                RestartSessionAction(
                    session_name=cast(str, SESSION_FIXTURE_DATA.name),
                    owner_access_key=cast(AccessKey, SESSION_FIXTURE_DATA.access_key),
                ),
                RestartSessionActionResult(
                    result=RESTART_SESSION_MOCK,
                    session_data=SESSION_FIXTURE_DATA,
                ),
            ),
            RESTART_SESSION_MOCK,
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
async def test_restart_session(
    mock_restart_session_rpc,
    mock_increment_session_usage_rpc,
    processors: SessionProcessors,
    test_scenario: TestScenario[RestartSessionAction, RestartSessionActionResult],
):
    # Expected result will use the session data from the database fixture
    assert test_scenario.expected is not None
    test_scenario.expected.session_data = SESSION_FIXTURE_DATA
    await test_scenario.test(processors.restart_session.wait_for_complete)
