from typing import cast
from unittest.mock import AsyncMock

import pytest

from ai.backend.common.types import AccessKey
from ai.backend.manager.services.session.actions.download_file import (
    DownloadFileAction,
    DownloadFileActionResult,
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
def mock_agent_download_single_rpc(mocker, mock_agent_response_result):
    mock = mocker.patch(
        "ai.backend.manager.registry.AgentRegistry.download_single",
        new_callable=AsyncMock,
    )
    mock.return_value = mock_agent_response_result
    return mock


AGENT_DOWNLOAD_FILE_RPC_RESP = b"file content"


@pytest.mark.parametrize(
    ("test_scenario", "mock_agent_response_result"),
    [
        (
            ScenarioBase.success(
                "List files",
                DownloadFileAction(
                    user_id=SESSION_FIXTURE_DATA.user_uuid,
                    file="example.txt",
                    session_name=cast(str, SESSION_FIXTURE_DATA.name),
                    owner_access_key=cast(AccessKey, SESSION_FIXTURE_DATA.access_key),
                ),
                DownloadFileActionResult(
                    bytes=AGENT_DOWNLOAD_FILE_RPC_RESP,
                    session_data=SESSION_FIXTURE_DATA,
                ),
            ),
            AGENT_DOWNLOAD_FILE_RPC_RESP,
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
async def test_download_file(
    mock_agent_download_single_rpc,
    processors: SessionProcessors,
    test_scenario: ScenarioBase[DownloadFileAction, DownloadFileActionResult],
):
    await test_scenario.test(processors.download_file.wait_for_complete)
