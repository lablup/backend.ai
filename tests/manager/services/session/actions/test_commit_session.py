from typing import cast
from unittest.mock import AsyncMock

import pytest

from ai.backend.common.types import AccessKey
from ai.backend.manager.services.session.actions.commit_session import (
    CommitSessionAction,
    CommitSessionActionResult,
)
from ai.backend.manager.services.session.processors import SessionProcessors

from ...test_utils import TestScenario
from ..fixtures import (
    KERNEL_FIXTURE_DICT,
    SESSION_FIXTURE_DATA,
    SESSION_FIXTURE_DICT,
)


@pytest.fixture
def mock_commit_session_to_file_rpc(mocker, mock_agent_response_result):
    mock = mocker.patch(
        "ai.backend.manager.registry.AgentRegistry.commit_session_to_file",
        new_callable=AsyncMock,
    )
    mock.return_value = mock_agent_response_result
    return mock


COMMIT_SESSION_MOCK = {"committed": True}


COMMIT_SESSION_ACTION = CommitSessionAction(
    session_name=cast(str, SESSION_FIXTURE_DATA.name),
    owner_access_key=cast(AccessKey, SESSION_FIXTURE_DATA.access_key),
    filename="test_file.py",
)


@pytest.mark.parametrize(
    ("test_scenario", "mock_agent_response_result"),
    [
        (
            TestScenario.success(
                "Commit session",
                COMMIT_SESSION_ACTION,
                CommitSessionActionResult(
                    session_data=SESSION_FIXTURE_DATA,
                    commit_result=COMMIT_SESSION_MOCK,
                ),
            ),
            COMMIT_SESSION_MOCK,
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
async def test_commit_session(
    mock_commit_session_to_file_rpc,
    processors: SessionProcessors,
    test_scenario: TestScenario[CommitSessionAction, CommitSessionActionResult],
):
    await test_scenario.test(processors.commit_session.wait_for_complete)
