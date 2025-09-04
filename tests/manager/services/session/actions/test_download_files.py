from typing import cast
from unittest.mock import AsyncMock

import pytest

from ai.backend.common.types import AccessKey
from ai.backend.manager.services.session.actions.download_files import (
    DownloadFilesAction,
    DownloadFilesActionResult,
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
def mock_download_file_rpc(mocker, mock_agent_response_result):
    mock = mocker.patch(
        "ai.backend.manager.registry.AgentRegistry.download_file",
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


DOWNLOAD_FILES_MOCK = b"test file content"


DOWNLOAD_FILES_ACTION = DownloadFilesAction(
    user_id=SESSION_FIXTURE_DATA.user_uuid,
    session_name=cast(str, SESSION_FIXTURE_DATA.name),
    owner_access_key=cast(AccessKey, SESSION_FIXTURE_DATA.access_key),
    files=["test_file1.txt", "test_file2.txt"],
)


@pytest.mark.parametrize(
    ("test_scenario", "mock_agent_response_result"),
    [
        (
            ScenarioBase.success(
                "Download files",
                DOWNLOAD_FILES_ACTION,
                DownloadFilesActionResult(
                    session_data=SESSION_FIXTURE_DATA,
                    result=None,  # Will be validated separately
                ),
            ),
            DOWNLOAD_FILES_MOCK,
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
async def test_download_files(
    mock_increment_session_usage_rpc,
    mock_download_file_rpc,
    processors: SessionProcessors,
    test_scenario: ScenarioBase[DownloadFilesAction, DownloadFilesActionResult],
):
    # Custom test to handle MultipartWriter comparison
    result = await processors.download_files.wait_for_complete(test_scenario.input)

    # Verify the result
    assert result is not None
    assert isinstance(result, DownloadFilesActionResult)
    assert result.session_data is not None
    assert result.result is not None  # MultipartWriter should be present

    # Verify the mocks were called correctly
    mock_increment_session_usage_rpc.assert_called_once()
    mock_download_file_rpc.assert_called()
