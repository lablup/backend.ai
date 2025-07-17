from typing import cast
from unittest.mock import AsyncMock

import pytest

from ai.backend.common.types import AccessKey
from ai.backend.manager.services.session.actions.commit_session import (
    CommitSessionAction,
    CommitSessionActionResult,
)
from ai.backend.manager.services.session.processors import SessionProcessors

from ..fixtures import (
    KERNEL_FIXTURE_DICT,
    SESSION_FIXTURE_DATA,
    SESSION_FIXTURE_DICT,
)


@pytest.fixture
def mock_agent_commit_session_rpc(mocker):
    mock = mocker.patch(
        "ai.backend.manager.registry.AgentRegistry.commit_session_to_file",
        new_callable=AsyncMock,
    )
    return mock


COMMIT_SESSION_MOCK = {"committed": True}


@pytest.mark.parametrize(
    "extra_fixtures",
    [
        {
            "sessions": [SESSION_FIXTURE_DICT],
            "kernels": [KERNEL_FIXTURE_DICT],
        }
    ],
)
async def test_commit_session(
    mock_agent_commit_session_rpc,
    processors: SessionProcessors,
):
    # Setup mock to return expected commit result
    mock_agent_commit_session_rpc.return_value = COMMIT_SESSION_MOCK

    # Create the action
    action = CommitSessionAction(
        session_name=cast(str, SESSION_FIXTURE_DATA.name),
        owner_access_key=cast(AccessKey, SESSION_FIXTURE_DATA.access_key),
        filename="test_file.py",
    )

    # Execute the action
    result = await processors.commit_session.wait_for_complete(action)

    # Assert the result is correct
    assert result is not None
    assert isinstance(result, CommitSessionActionResult)
    assert result.commit_result == COMMIT_SESSION_MOCK

    # Verify the session_row contains the expected session data
    assert result.session_row is not None
    assert str(result.session_row.id) == str(SESSION_FIXTURE_DATA.id)
    assert result.session_row.name == SESSION_FIXTURE_DATA.name
    assert result.session_row.access_key == SESSION_FIXTURE_DATA.access_key

    # Verify the mock was called correctly
    mock_agent_commit_session_rpc.assert_called_once()
