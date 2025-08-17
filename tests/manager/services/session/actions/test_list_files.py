from typing import cast
from unittest.mock import AsyncMock

import pytest

from ai.backend.common.types import AccessKey
from ai.backend.manager.services.session.actions.list_files import (
    ListFilesAction,
    ListFilesActionResult,
)
from ai.backend.manager.services.session.processors import SessionProcessors

from ...utils import ScenarioBase
from ..fixtures import KERNEL_FIXTURE_DICT, SESSION_FIXTURE_DATA, SESSION_FIXTURE_DICT


@pytest.fixture
def mock_list_files_rpc(mocker, mock_agent_response_result):
    mock = mocker.patch(
        "ai.backend.manager.registry.AgentRegistry.list_files",
        new_callable=AsyncMock,
    )
    mock.return_value = mock_agent_response_result
    return mock


AGENT_LIST_FILES_RPC_RESP = {
    "files": [
        {
            "mode": "-rw-------",
            "size": 1234,
            "ctime": 0.0,
            "mtime": 0.0,
            "atime": 0.0,
            "filename": "example.txt",
        }
    ]
}


@pytest.mark.parametrize(
    ("test_scenario", "mock_agent_response_result"),
    [
        (
            ScenarioBase.success(
                "List files",
                ListFilesAction(
                    user_id=SESSION_FIXTURE_DATA.user_uuid,
                    path=".",
                    session_name=cast(str, SESSION_FIXTURE_DATA.name),
                    owner_access_key=cast(AccessKey, SESSION_FIXTURE_DATA.access_key),
                ),
                ListFilesActionResult(
                    result=AGENT_LIST_FILES_RPC_RESP,
                    session_data=SESSION_FIXTURE_DATA,
                ),
            ),
            AGENT_LIST_FILES_RPC_RESP,
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
async def test_list_files(
    mock_list_files_rpc,
    processors: SessionProcessors,
    test_scenario: ScenarioBase[ListFilesAction, ListFilesActionResult],
):
    await test_scenario.test(processors.list_files.wait_for_complete)
