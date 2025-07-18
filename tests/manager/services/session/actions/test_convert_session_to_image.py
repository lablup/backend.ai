from typing import cast
from unittest.mock import AsyncMock, MagicMock
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
def mock_group_with_container_registry(mocker):
    """Mock the group's container_registry to be populated"""
    mock = mocker.patch(
        "ai.backend.manager.repositories.session.repository.SessionRepository.get_session_with_group",
        new_callable=AsyncMock,
    )

    # Create a mock session with a group that has container registry
    mock_session = MagicMock()
    mock_session.name = SESSION_FIXTURE_DATA.name
    mock_session.id = SESSION_FIXTURE_DATA.id
    mock_session.access_key = SESSION_FIXTURE_DATA.access_key
    mock_session.main_kernel.image = "registry.example.com/test_project/python:3.9"
    mock_session.main_kernel.architecture = "x86_64"
    mock_session.group = MagicMock()
    mock_session.group.container_registry = {
        "registry": "registry.example.com",
        "project": "test_project",
    }

    mock.return_value = mock_session
    return mock


@pytest.fixture
def mock_resolve_image(mocker):
    mock_image_row = MagicMock()
    mock_image_row.id = "test_image_id"
    mock_image_row.canonical = "registry.example.com/test_project/python:3.9"
    mock_image_row.architecture = "x86_64"

    mock = mocker.patch(
        "ai.backend.manager.repositories.session.repository.SessionRepository.resolve_image",
        new_callable=AsyncMock,
        return_value=mock_image_row,
    )
    return mock


@pytest.fixture
def mock_agent_convert_session_to_image_rpc(mocker):
    mock = mocker.patch(
        "ai.backend.manager.registry.AgentRegistry.commit_session",
        new_callable=AsyncMock,
    )
    return mock


@pytest.fixture
def mock_background_task_manager(mocker):
    mock = mocker.patch(
        "ai.backend.common.bgtask.bgtask.BackgroundTaskManager.start",
        new_callable=AsyncMock,
        return_value=CONVERT_SESSION_TO_IMAGE_MOCK,
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
    mock_agent_convert_session_to_image_rpc,
    mock_group_with_container_registry,
    mock_resolve_image,
    mock_background_task_manager,
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

    # Verify the session_data contains the expected session data
    assert result.session_data is not None
    assert str(result.session_data.id) == str(SESSION_FIXTURE_DATA.id)
    assert result.session_data.name == SESSION_FIXTURE_DATA.name
    assert result.session_data.access_key == SESSION_FIXTURE_DATA.access_key

    # Verify the mock was called correctly
    mock_agent_convert_session_to_image_rpc.assert_called_once()
