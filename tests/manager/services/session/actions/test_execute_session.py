from typing import cast
from unittest.mock import AsyncMock

import pytest

from ai.backend.common.types import AccessKey
from ai.backend.manager.services.session.actions.execute_session import (
    ExecuteSessionAction,
    ExecuteSessionActionParams,
    ExecuteSessionActionResult,
)
from ai.backend.manager.services.session.processors import SessionProcessors

from ...test_utils import TestScenario
from ..fixtures import (
    KERNEL_FIXTURE_DICT,
    SESSION_FIXTURE_DATA,
    SESSION_FIXTURE_DICT,
    SESSION_ROW_FIXTURE,
)


@pytest.fixture
def mock_agent_execute_session_rpc(mocker, mock_agent_response_result):
    mock = mocker.patch(
        "ai.backend.manager.registry.AgentRegistry.execute_session",
        new_callable=AsyncMock,
    )
    mock.return_value = mock_agent_response_result
    return mock


EXECUTE_SESSION_MOCK = {"status": "finished", "result": {"output": "Hello World"}}


@pytest.mark.parametrize(
    ("test_scenario", "mock_agent_response_result"),
    [
        (
            TestScenario.success(
                "Execute session",
                ExecuteSessionAction(
                    session_name=cast(str, SESSION_FIXTURE_DATA.name),
                    api_version=(1, 0),
                    owner_access_key=cast(AccessKey, SESSION_FIXTURE_DATA.access_key),
                    params=ExecuteSessionActionParams(
                        mode="query",
                        options=None,
                        code="print('Hello World')",
                        run_id="test_run_123",
                    ),
                ),
                ExecuteSessionActionResult(
                    result=EXECUTE_SESSION_MOCK,
                    session_row=SESSION_ROW_FIXTURE,
                ),
            ),
            EXECUTE_SESSION_MOCK,
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
async def test_execute_session(
    mock_agent_execute_session_rpc,
    processors: SessionProcessors,
    test_scenario: TestScenario[ExecuteSessionAction, ExecuteSessionActionResult],
):
    await test_scenario.test(processors.execute_session.wait_for_complete)
