from typing import cast
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.types import AccessKey
from ai.backend.manager.services.session.actions.upload_files import (
    UploadFilesAction,
    UploadFilesActionResult,
)
from ai.backend.manager.services.session.processors import SessionProcessors

from ...test_utils import TestScenario
from ..fixtures import (
    KERNEL_FIXTURE_DICT,
    SESSION_FIXTURE_DATA,
    SESSION_FIXTURE_DICT,
)


@pytest.fixture
def mock_upload_files_rpc(mocker, mock_agent_response_result):
    # Mock the upload_files service method directly
    from ai.backend.manager.services.session.service import SessionService

    mock_upload_files = mocker.patch.object(
        SessionService,
        "upload_files",
        new_callable=AsyncMock,
    )

    from ai.backend.manager.services.session.actions.upload_files import (
        UploadFilesActionResult,
    )

    mock_upload_files.return_value = UploadFilesActionResult(
        result=mock_agent_response_result,
        session_data=SESSION_FIXTURE_DATA,
    )

    return mock_agent_response_result


@pytest.fixture
def mock_large_file_reader():
    """Mock a MultipartReader with a large file"""
    mock_reader = MagicMock()
    mock_file = MagicMock()
    mock_file.filename = "large_file.txt"
    mock_file.read_chunk = AsyncMock(return_value=b"x" * 1048577)  # > 1MB
    mock_file.decode = MagicMock(return_value="large content")

    async def mock_next():
        yield mock_file

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
    ("test_scenario", "mock_agent_response_result"),
    [
        (
            TestScenario.success(
                "Upload files",
                UploadFilesAction(
                    session_name=cast(str, SESSION_FIXTURE_DATA.name),
                    owner_access_key=cast(AccessKey, SESSION_FIXTURE_DATA.access_key),
                    reader=MagicMock(),  # Mock MultipartReader
                ),
                UploadFilesActionResult(
                    result=UPLOAD_FILES_MOCK,
                    session_data=SESSION_FIXTURE_DATA,
                ),
            ),
            UPLOAD_FILES_MOCK,
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
async def test_upload_files(
    mock_upload_files_rpc,
    processors: SessionProcessors,
    test_scenario: TestScenario[UploadFilesAction, UploadFilesActionResult],
):
    # Expected result will use the session data from the database fixture
    assert test_scenario.expected is not None
    test_scenario.expected.session_data = SESSION_FIXTURE_DATA
    await test_scenario.test(processors.upload_files.wait_for_complete)
