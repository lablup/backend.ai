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
    mock = mocker.patch(
        "ai.backend.manager.registry.AgentRegistry.upload_files",
        new_callable=AsyncMock,
    )
    mock.return_value = mock_agent_response_result
    return mock


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
    await test_scenario.test(processors.upload_files.wait_for_complete)
