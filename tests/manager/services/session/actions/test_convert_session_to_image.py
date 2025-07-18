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

from ...fixtures import (
    CONTAINER_REGISTRY_FIXTURE_DICT,
    IMAGE_FIXTURE_DICT,
)
from ..fixtures import (
    KERNEL_FIXTURE_DICT,
    SESSION_FIXTURE_DATA,
    SESSION_FIXTURE_DICT,
)


@pytest.fixture
def mock_convert_session_to_image_service(mocker):
    mock = mocker.patch(
        "ai.backend.manager.services.session.service.SessionService.convert_session_to_image",
        new_callable=AsyncMock,
    )
    mock.return_value = ConvertSessionToImageActionResult(
        task_id=CONVERT_SESSION_TO_IMAGE_MOCK,
        session_data=SESSION_FIXTURE_DATA,
    )
    return mock


CONVERT_SESSION_TO_IMAGE_MOCK = uuid4()


@pytest.mark.parametrize(
    "extra_fixtures",
    [
        {
            "sessions": [SESSION_FIXTURE_DICT],
            "kernels": [KERNEL_FIXTURE_DICT],
            "container_registries": [CONTAINER_REGISTRY_FIXTURE_DICT],
            "images": [IMAGE_FIXTURE_DICT],
        }
    ],
)
async def test_convert_session_to_image(
    mock_convert_session_to_image_service,
    processors: SessionProcessors,
):
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

    # Verify the session_data contains the expected session data
    assert result.session_data is not None
    assert str(result.session_data.id) == str(SESSION_FIXTURE_DATA.id)
    assert result.session_data.name == SESSION_FIXTURE_DATA.name
    assert result.session_data.access_key == SESSION_FIXTURE_DATA.access_key

    # Verify the mock was called correctly
    mock_convert_session_to_image_service.assert_called_once()
