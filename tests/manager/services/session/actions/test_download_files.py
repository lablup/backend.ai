from typing import cast
from unittest.mock import AsyncMock

import pytest

from ai.backend.common.types import AccessKey
from ai.backend.manager.services.session.actions.download_files import (
    DownloadFilesAction,
    DownloadFilesActionResult,
)
from ai.backend.manager.services.session.processors import SessionProcessors

from ...test_utils import TestScenario
from ..fixtures import (
    KERNEL_FIXTURE_DICT,
    SESSION_FIXTURE_DATA,
    SESSION_FIXTURE_DICT,
    SESSION_ROW_FIXTURE,
)


@pytest.fixture
def mock_agent_download_files_rpc(mocker, mock_agent_response_result):
    mock = mocker.patch(
        "ai.backend.manager.registry.AgentRegistry.download_files",
        new_callable=AsyncMock,
    )
    mock.return_value = mock_agent_response_result
    return mock


DOWNLOAD_FILES_MOCK = b"test file content"


@pytest.mark.parametrize(
    ("test_scenario", "mock_agent_response_result"),
    [
        (
            TestScenario.success(
                "Download files",
                DownloadFilesAction(
                    user_id=SESSION_FIXTURE_DATA.user_uuid,
                    session_name=cast(str, SESSION_FIXTURE_DATA.name),
                    owner_access_key=cast(AccessKey, SESSION_FIXTURE_DATA.access_key),
                    files=["test_file1.txt", "test_file2.txt"],
                ),
                DownloadFilesActionResult(
                    result=DOWNLOAD_FILES_MOCK,
                    session_row=SESSION_ROW_FIXTURE,
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
            "sessions": [SESSION_FIXTURE_DICT],
            "kernels": [KERNEL_FIXTURE_DICT],
        }
    ],
)
async def test_download_files(
    mock_agent_download_files_rpc,
    processors: SessionProcessors,
    test_scenario: TestScenario[DownloadFilesAction, DownloadFilesActionResult],
):
    await test_scenario.test(processors.download_files.wait_for_complete)
