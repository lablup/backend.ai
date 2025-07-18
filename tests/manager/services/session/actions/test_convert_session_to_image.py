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
    # Since this is a very complex service method with background tasks,
    # let's mock the key dependencies but keep the test simpler
    from ai.backend.common.docker import ImageRef
    from ai.backend.manager.models.group import GroupRow
    from ai.backend.manager.models.kernel import KernelRow
    from ai.backend.manager.models.session import SessionRow
    from ai.backend.manager.services.session.service import SessionService

    # Create mock objects
    mock_session = SessionRow(**SESSION_FIXTURE_DICT)
    mock_kernel = KernelRow(**KERNEL_FIXTURE_DICT)
    mock_session.kernels = [mock_kernel]

    # Create a mock group with container registry
    mock_group = GroupRow(
        id=SESSION_FIXTURE_DATA.group_id,
        name="test_group",
        domain_name="default",
        container_registry={"registry": "test-registry.com", "project": "test-project"},
    )
    mock_session.group = mock_group

    # Mock repository methods
    mock_get_session_with_group = mocker.patch(
        "ai.backend.manager.repositories.session.repository.SessionRepository.get_session_with_group",
        new_callable=AsyncMock,
    )
    mock_get_session_with_group.return_value = mock_session

    mock_get_container_registry = mocker.patch(
        "ai.backend.manager.repositories.session.repository.SessionRepository.get_container_registry",
        new_callable=AsyncMock,
    )
    mock_get_container_registry.return_value = {
        "registry": "test-registry.com",
        "project": "test-project",
    }

    # Mock resolve_image with a simpler mock object
    mock_resolve_image = mocker.patch(
        "ai.backend.manager.repositories.session.repository.SessionRepository.resolve_image",
        new_callable=AsyncMock,
    )
    mock_image_row = type(
        "MockImageRow",
        (),
        {
            "image_ref": ImageRef(
                name="test-image",
                project="test-project",
                tag="latest",
                registry="test-registry.com",
                architecture="x86_64",
                is_local=False,
            )
        },
    )()
    mock_resolve_image.return_value = mock_image_row

    # Mock background task manager
    mock_bgtask_manager = mocker.patch.object(
        SessionService, "_background_task_manager", create=True
    )
    mock_bgtask_manager.start = AsyncMock(return_value=CONVERT_SESSION_TO_IMAGE_MOCK)

    return {
        "get_session_with_group": mock_get_session_with_group,
        "get_container_registry": mock_get_container_registry,
        "resolve_image": mock_resolve_image,
        "bgtask_manager": mock_bgtask_manager,
        "session": mock_session,
    }


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
    expected_session_data = mock_convert_session_to_image_service["session"].to_dataclass()
    assert result.session_data.id == expected_session_data.id
    assert result.session_data.name == expected_session_data.name
    assert result.session_data.access_key == expected_session_data.access_key

    # Verify the mocks were called correctly
    mock_convert_session_to_image_service["get_session_with_group"].assert_called_once()
    mock_convert_session_to_image_service["get_container_registry"].assert_called_once()
    mock_convert_session_to_image_service["resolve_image"].assert_called_once()
    mock_convert_session_to_image_service["bgtask_manager"].start.assert_called_once()
