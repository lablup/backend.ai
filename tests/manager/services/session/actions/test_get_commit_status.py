from typing import cast
from unittest.mock import AsyncMock

import pytest

from ai.backend.common.types import AccessKey, CommitStatus
from ai.backend.manager.services.session.actions.get_commit_status import (
    GetCommitStatusAction,
    GetCommitStatusActionResult,
)
from ai.backend.manager.services.session.processors import SessionProcessors
from ai.backend.manager.services.session.types import CommitStatusInfo

from ...test_utils import TestScenario
from ..fixtures import (
    KERNEL_FIXTURE_DATA,
    KERNEL_FIXTURE_DICT,
    SESSION_FIXTURE_DATA,
    SESSION_FIXTURE_DICT,
)


@pytest.fixture
def mock_agent_get_commit_status_rpc(mocker, mock_agent_response_result):
    mock = mocker.patch(
        "ai.backend.manager.registry.AgentRegistry.get_commit_status",
        new_callable=AsyncMock,
    )
    mock.return_value = mock_agent_response_result
    return mock


AGENT_COMMIT_STATUS_RPC_RESP = {
    KERNEL_FIXTURE_DATA.id: CommitStatus.READY,
}


@pytest.mark.parametrize(
    ("test_scenario", "mock_agent_response_result"),
    [
        (
            TestScenario.success(
                "List files",
                GetCommitStatusAction(
                    session_name=cast(str, SESSION_FIXTURE_DATA.name),
                    owner_access_key=cast(AccessKey, SESSION_FIXTURE_DATA.access_key),
                ),
                GetCommitStatusActionResult(
                    commit_info=CommitStatusInfo(
                        status="ready",
                        kernel=str(KERNEL_FIXTURE_DATA.id),
                    ),
                    session_data=SESSION_FIXTURE_DATA,
                ),
            ),
            AGENT_COMMIT_STATUS_RPC_RESP,
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
async def test_get_commit_status(
    mock_agent_get_commit_status_rpc,
    processors: SessionProcessors,
    test_scenario: TestScenario[GetCommitStatusAction, GetCommitStatusActionResult],
):
    await test_scenario.test(processors.get_commit_status.wait_for_complete)
