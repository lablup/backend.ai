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

from ..fixtures import (
    KERNEL_FIXTURE_DICT,
    SESSION_FIXTURE_DATA,
    SESSION_FIXTURE_DICT,
)


@pytest.fixture
def mock_agent_convert_session_to_image_rpc(mocker):
    mock = mocker.patch(
        "ai.backend.manager.registry.AgentRegistry.commit_session",
        new_callable=AsyncMock,
    )
    return mock


CONVERT_SESSION_TO_IMAGE_MOCK = uuid4()


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
):
    # Setup mock to return expected task ID
    mock_agent_convert_session_to_image_rpc.return_value = CONVERT_SESSION_TO_IMAGE_MOCK

    # Create the action
    action = ConvertSessionToImageAction(
        session_name=cast(str, SESSION_FIXTURE_DATA.name),
        owner_access_key=cast(AccessKey, SESSION_FIXTURE_DATA.access_key),
        image_name="test_image",
        image_visibility=CustomizedImageVisibilityScope.USER,
        image_owner_id=SESSION_FIXTURE_DATA.user_uuid,
        user_email="test@example.com",
        max_customized_image_count=10,
    )

    # Execute the action
    result = await processors.convert_session_to_image.wait_for_complete(action)

    # Assert the result is correct
    assert result is not None
    assert isinstance(result, ConvertSessionToImageActionResult)
    assert result.task_id == CONVERT_SESSION_TO_IMAGE_MOCK

    # Verify the session_row contains the expected session data
    assert result.session_row is not None
    assert str(result.session_row.id) == str(SESSION_FIXTURE_DATA.id)
    assert result.session_row.name == SESSION_FIXTURE_DATA.name
    assert result.session_row.access_key == SESSION_FIXTURE_DATA.access_key

    # Verify the mock was called correctly
    mock_agent_convert_session_to_image_rpc.assert_called_once()
