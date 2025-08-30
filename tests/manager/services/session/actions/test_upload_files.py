from typing import cast
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiohttp import MultipartReader

from ai.backend.common.types import AccessKey
from ai.backend.manager.services.session.actions.upload_files import (
    UploadFilesAction,
    UploadFilesActionResult,
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
def mock_upload_file_rpc(mocker):
    # Mock increment_session_usage
    mock_increment_usage = mocker.patch(
        "ai.backend.manager.registry.AgentRegistry.increment_session_usage",
        new_callable=AsyncMock,
    )

    # Mock upload_file (called for each file)
    mock_upload_file = mocker.patch(
        "ai.backend.manager.registry.AgentRegistry.upload_file",
        new_callable=AsyncMock,
    )

    return {
        "increment_usage": mock_increment_usage,
        "upload_file": mock_upload_file,
    }


@pytest.fixture
def mock_simple_file_reader():
    """Mock a MultipartReader with simple files"""
    mock_reader = MagicMock()

    # Create a simple test file
    mock_file = MagicMock()
    mock_file.filename = "test_file.txt"
    mock_file.read_chunk = AsyncMock(
        side_effect=[b"test content", b""]
    )  # First call returns content, second returns empty
    mock_file.decode = MagicMock(return_value="test content")

    # Mock next method to work with aiotools.aiter(reader.next, None)
    call_count = 0

    async def mock_next():
        nonlocal call_count
        if call_count == 0:
            call_count += 1
            return mock_file
        else:
            return None  # Sentinel value to stop iteration

    mock_reader.next = mock_next
    return mock_reader


@pytest.fixture
def mock_too_many_files_reader():
    """Mock a MultipartReader with too many files"""
    mock_reader = MagicMock()

    async def mock_next():
        for i in range(21):  # More than 20 files
            mock_file = MagicMock()
            mock_file.filename = f"file_{i}.txt"
            mock_file.read_chunk = AsyncMock(return_value=b"small content")
            mock_file.decode = MagicMock(return_value="content")
            yield mock_file

    mock_reader.next = mock_next
    return mock_reader


UPLOAD_FILES_MOCK = {"uploaded": True, "files": ["test_file1.txt", "test_file2.txt"]}


@pytest.mark.parametrize(
    "test_scenario",
    [
        ScenarioBase.success(
            "Upload files",
            UploadFilesAction(
                session_name=cast(str, SESSION_FIXTURE_DATA.name),
                owner_access_key=cast(AccessKey, SESSION_FIXTURE_DATA.access_key),
                reader=cast(MultipartReader, None),  # Will be set in the test function
            ),
            UploadFilesActionResult(
                result=None,  # upload_files returns None in result
                session_data=SESSION_FIXTURE_DATA,
            ),
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
async def test_upload_files(
    mock_upload_file_rpc,
    mock_simple_file_reader,
    processors: SessionProcessors,
    test_scenario: ScenarioBase[UploadFilesAction, UploadFilesActionResult],
):
    # Set the reader in the test scenario
    test_scenario.input.reader = mock_simple_file_reader

    # Execute the action
    result = await processors.upload_files.wait_for_complete(test_scenario.input)

    # Verify the result
    assert result is not None
    assert isinstance(result, UploadFilesActionResult)
    assert result.result is None  # upload_files returns None in result

    # Verify session_data is properly returned
    assert result.session_data is not None
    assert result.session_data.id == SESSION_FIXTURE_DATA.id
    assert result.session_data.name == SESSION_FIXTURE_DATA.name
    assert result.session_data.access_key == SESSION_FIXTURE_DATA.access_key

    # Verify that agent RPC calls were made
    mock_upload_file_rpc["increment_usage"].assert_called_once()
    mock_upload_file_rpc["upload_file"].assert_called_once()
