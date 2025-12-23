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
)
from ..fixtures import (
    AGENT_FIXTURE_DICT,
    GROUP_FIXTURE_DATA,
    GROUP_USER_ASSOCIATION_DATA,
    KERNEL_FIXTURE_DICT,
    SESSION_FIXTURE_DATA,
    SESSION_FIXTURE_DICT,
    USER_FIXTURE_DATA,
)

SESSION_FIXTURE_DICT = {**SESSION_FIXTURE_DICT, "group_id": GROUP_FIXTURE_DATA["id"]}


@pytest.fixture
def mock_commit_session_rpc(mocker):
    mock = mocker.patch(
        "ai.backend.manager.registry.AgentRegistry.commit_session",
        new_callable=AsyncMock,
    )
    mock.return_value = {"bgtask_id": COMMIT_SESSION_MOCK_TASK_ID}
    return mock


@pytest.fixture
def mock_push_image_rpc(mocker):
    # Mock the push_image agent RPC call
    mock = mocker.patch(
        "ai.backend.manager.registry.AgentRegistry.push_image",
        new_callable=AsyncMock,
    )
    mock.return_value = {"bgtask_id": PUSH_IMAGE_MOCK_TASK_ID}
    return mock


COMMIT_SESSION_MOCK_TASK_ID = uuid4()
PUSH_IMAGE_MOCK_TASK_ID = uuid4()


@pytest.mark.skip(reason="WIP, Need to be fixed")
@pytest.mark.parametrize(
    "extra_fixtures",
    [
        {
            "container_registries": [CONTAINER_REGISTRY_FIXTURE_DICT],
            "agents": [AGENT_FIXTURE_DICT],
            "sessions": [SESSION_FIXTURE_DICT],
            "kernels": [KERNEL_FIXTURE_DICT],
            "users": [USER_FIXTURE_DATA],
            "groups": [GROUP_FIXTURE_DATA],
            "association_groups_users": [GROUP_USER_ASSOCIATION_DATA],
        }
    ],
)
async def test_convert_session_to_image(
    mock_commit_session_rpc,
    mock_push_image_rpc,
    processors: SessionProcessors,
    session_repository,
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
    assert result.task_id == COMMIT_SESSION_MOCK_TASK_ID

    # Verify the session_data contains the expected session data
    assert result.session_data is not None
    assert result.session_data.id == SESSION_FIXTURE_DATA.id
    assert result.session_data.name == SESSION_FIXTURE_DATA.name
    assert result.session_data.access_key == SESSION_FIXTURE_DATA.access_key
