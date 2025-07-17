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

from ..fixtures import (
    KERNEL_FIXTURE_DICT,
    SESSION_FIXTURE_DATA,
    SESSION_FIXTURE_DICT,
)


@pytest.fixture
def mock_agent_complete_session_rpc(mocker):
    mock = mocker.patch(
        "ai.backend.manager.registry.AgentRegistry.get_completions",
        new_callable=AsyncMock,
    )
    return mock


COMPLETE_SESSION_MOCK = CodeCompletionResp(
    result=CodeCompletionResult(
        status="finished",
        error=None,
        suggestions=["test_completion"],
    )
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
async def test_complete_session(
    mock_agent_complete_session_rpc,
    processors: SessionProcessors,
):
    # Setup mock to return expected completion result
    mock_agent_complete_session_rpc.return_value = COMPLETE_SESSION_MOCK

    # Create the action
    action = CompleteAction(
        session_name=cast(str, SESSION_FIXTURE_DATA.name),
        owner_access_key=cast(AccessKey, SESSION_FIXTURE_DATA.access_key),
        code="print('Hello')",
        options=None,
    )

    # Execute the action
    result = await processors.complete.wait_for_complete(action)

    # Assert the result is correct
    assert result is not None
    assert isinstance(result, CompleteActionResult)
    assert result.result == COMPLETE_SESSION_MOCK

    # Verify the session_row contains the expected session data
    assert result.session_row is not None
    assert str(result.session_row.id) == str(SESSION_FIXTURE_DATA.id)
    assert result.session_row.name == SESSION_FIXTURE_DATA.name
    assert result.session_row.access_key == SESSION_FIXTURE_DATA.access_key

    # Verify the mock was called correctly
    mock_agent_complete_session_rpc.assert_called_once()
