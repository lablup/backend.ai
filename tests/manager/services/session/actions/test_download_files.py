from typing import cast
from unittest.mock import AsyncMock

import pytest

from ai.backend.common.types import AccessKey
from ai.backend.manager.services.session.actions.download_files import (
    DownloadFilesAction,
    DownloadFilesActionResult,
)
from ai.backend.manager.services.session.processors import SessionProcessors

from ..fixtures import (
    KERNEL_FIXTURE_DICT,
    SESSION_FIXTURE_DATA,
    SESSION_FIXTURE_DICT,
)


@pytest.fixture
def mock_agent_download_files_rpc(mocker):
    mock = mocker.patch(
        "ai.backend.manager.registry.AgentRegistry.download_file",
        new_callable=AsyncMock,
    )
    return mock


DOWNLOAD_FILES_MOCK = b"test file content"


@pytest.mark.parametrize(
    "extra_fixtures",
    [
        {
            "sessions": [SESSION_FIXTURE_DICT],
            "kernels": [KERNEL_FIXTURE_DICT],
        }
    ],
)
async def test_download_files(
    mock_agent_download_files_rpc,
    processors: SessionProcessors,
):
    # Setup mock to return expected download result
    mock_agent_download_files_rpc.return_value = DOWNLOAD_FILES_MOCK

    # Create the action
    action = DownloadFilesAction(
        user_id=SESSION_FIXTURE_DATA.user_uuid,
        session_name=cast(str, SESSION_FIXTURE_DATA.name),
        owner_access_key=cast(AccessKey, SESSION_FIXTURE_DATA.access_key),
        files=["test_file1.txt", "test_file2.txt"],
    )

    # Execute the action
    result = await processors.download_files.wait_for_complete(action)

    # Assert the result is correct
    assert result is not None
    assert isinstance(result, DownloadFilesActionResult)
    assert result.result is not None  # Should be a MultipartWriter

    # Verify the session_row contains the expected session data
    assert result.session_row is not None
    assert str(result.session_row.id) == str(SESSION_FIXTURE_DATA.id)
    assert result.session_row.name == SESSION_FIXTURE_DATA.name
    assert result.session_row.access_key == SESSION_FIXTURE_DATA.access_key

    # Verify the mock was called correctly
    mock_agent_download_files_rpc.assert_called()
