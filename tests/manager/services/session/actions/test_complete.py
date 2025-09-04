from typing import cast
from unittest.mock import AsyncMock

import pytest

from ai.backend.common.dto.agent.response import CodeCompletionResp, CodeCompletionResult
from ai.backend.common.types import AccessKey
from ai.backend.manager.services.session.actions.complete import (
    CompleteAction,
    CompleteActionResult,
)
from ai.backend.manager.services.session.processors import SessionProcessors

from ...utils import ScenarioBase
from ..fixtures import (
    AGENT_FIXTURE_DICT,
    KERNEL_FIXTURE_DICT,
    SESSION_FIXTURE_DATA,
    SESSION_FIXTURE_DICT,
)


@pytest.fixture
def mock_complete_session_rpc(mocker, mock_agent_response_result):
    mock = mocker.patch(
        "ai.backend.manager.registry.AgentRegistry.get_completions",
        new_callable=AsyncMock,
    )
    mock.return_value = mock_agent_response_result
    return mock


@pytest.fixture
def mock_increment_session_usage_rpc(mocker, mock_agent_response_result):
    mock_increment_usage = mocker.patch(
        "ai.backend.manager.registry.AgentRegistry.increment_session_usage",
        new_callable=AsyncMock,
    )
    return mock_increment_usage


COMPLETE_SESSION_MOCK = CodeCompletionResp(
    result=CodeCompletionResult(
        status="finished",
        error=None,
        suggestions=["test_completion"],
    )
)


COMPLETE_ACTION = CompleteAction(
    session_name=cast(str, SESSION_FIXTURE_DATA.name),
    owner_access_key=cast(AccessKey, SESSION_FIXTURE_DATA.access_key),
    code="print('Hello')",
    options=None,
)


@pytest.mark.parametrize(
    ("test_scenario", "mock_agent_response_result"),
    [
        (
            ScenarioBase.success(
                "Complete session",
                COMPLETE_ACTION,
                CompleteActionResult(
                    session_data=SESSION_FIXTURE_DATA,
                    result=COMPLETE_SESSION_MOCK,
                ),
            ),
            COMPLETE_SESSION_MOCK,
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
        }
    ],
)
async def test_complete_session(
    mock_increment_session_usage_rpc,
    mock_complete_session_rpc,
    processors: SessionProcessors,
    test_scenario: ScenarioBase[CompleteAction, CompleteActionResult],
):
    # Execute the actual service
    result = await processors.complete.wait_for_complete(test_scenario.input)

    # Verify the result
    assert result is not None
    assert isinstance(result, CompleteActionResult)
    assert result.session_data is not None
    assert result.result is not None
    assert result.result == COMPLETE_SESSION_MOCK

    # Verify the mocks were called
    mock_increment_session_usage_rpc.assert_called_once()
    mock_complete_session_rpc.assert_called_once()
