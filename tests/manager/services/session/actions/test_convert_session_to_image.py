from typing import cast
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from ai.backend.common.data.session.types import CustomizedImageVisibilityScope
from ai.backend.common.types import AccessKey
from ai.backend.manager.services.session.actions.convert_session_to_image import (
    ConvertSessionToImageAction,
    ConvertSessionToImageActionResult,
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
def mock_agent_convert_session_to_image_rpc(mocker, mock_agent_response_result):
    mock = mocker.patch(
        "ai.backend.manager.registry.AgentRegistry.convert_session_to_image",
        new_callable=AsyncMock,
    )
    mock.return_value = mock_agent_response_result
    return mock


CONVERT_SESSION_TO_IMAGE_MOCK = uuid4()


@pytest.mark.parametrize(
    ("test_scenario", "mock_agent_response_result"),
    [
        (
            TestScenario.success(
                "Convert session to image",
                ConvertSessionToImageAction(
                    session_name=cast(str, SESSION_FIXTURE_DATA.name),
                    owner_access_key=cast(AccessKey, SESSION_FIXTURE_DATA.access_key),
                    image_name="test_image",
                    image_visibility=CustomizedImageVisibilityScope.USER,
                    image_owner_id=SESSION_FIXTURE_DATA.user_uuid,
                    user_email="test@example.com",
                    max_customized_image_count=10,
                ),
                ConvertSessionToImageActionResult(
                    task_id=CONVERT_SESSION_TO_IMAGE_MOCK,
                    session_row=SESSION_ROW_FIXTURE,
                ),
            ),
            CONVERT_SESSION_TO_IMAGE_MOCK,
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
async def test_convert_session_to_image(
    mock_agent_convert_session_to_image_rpc,
    processors: SessionProcessors,
    test_scenario: TestScenario[ConvertSessionToImageAction, ConvertSessionToImageActionResult],
):
    await test_scenario.test(processors.convert_session_to_image.wait_for_complete)
