from typing import cast
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from ai.backend.common.types import AccessKey, SessionTypes
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.services.session.actions.create_cluster import (
    CreateClusterAction,
    CreateClusterActionResult,
)
from ai.backend.manager.services.session.processors import SessionProcessors

from ..fixtures import (
    KERNEL_FIXTURE_DICT,
    SESSION_FIXTURE_DATA,
    SESSION_FIXTURE_DICT,
)


@pytest.fixture
def mock_create_cluster_rpc(mocker):
    mock = mocker.patch(
        "ai.backend.manager.registry.AgentRegistry.create_cluster",
        new_callable=AsyncMock,
    )
    return mock


@pytest.fixture
def mock_get_template_by_id(mocker):
    mock_template = MagicMock()
    mock_template.id = TEST_TEMPLATE_ID
    mock_template.name = "test_template"
    mock_template.task_definition = {
        "image": "python:3.9",
        "command": ["python", "-c", "print('hello')"],
    }

    mock = mocker.patch(
        "ai.backend.manager.repositories.session.repository.SessionRepository.get_template_by_id",
        new_callable=AsyncMock,
        return_value=mock_template,
    )
    return mock


CREATE_CLUSTER_MOCK = {"cluster_id": "test_cluster_123"}
TEST_TEMPLATE_ID = uuid4()


@pytest.mark.parametrize(
    "extra_fixtures",
    [
        {
            "sessions": [SESSION_FIXTURE_DICT],
            "kernels": [KERNEL_FIXTURE_DICT],
        }
    ],
)
async def test_create_cluster(
    mock_create_cluster_rpc,
    mock_get_template_by_id,
    processors: SessionProcessors,
):
    # Setup mock to return expected cluster result
    mock_create_cluster_rpc.return_value = CREATE_CLUSTER_MOCK

    # Create the action
    action = CreateClusterAction(
        session_name=cast(str, SESSION_FIXTURE_DATA.name),
        user_id=SESSION_FIXTURE_DATA.user_uuid,
        user_role=UserRole.USER,
        sudo_session_enabled=False,
        template_id=TEST_TEMPLATE_ID,
        session_type=SessionTypes.INTERACTIVE,
        group_name=str(SESSION_FIXTURE_DATA.group_id),
        domain_name=SESSION_FIXTURE_DATA.domain_name,
        scaling_group_name="default",
        requester_access_key=cast(AccessKey, SESSION_FIXTURE_DATA.access_key),
        owner_access_key=cast(AccessKey, SESSION_FIXTURE_DATA.access_key),
        tag="latest",
        enqueue_only=False,
        keypair_resource_policy=None,
        max_wait_seconds=0,
    )

    # Execute the action
    result = await processors.create_cluster.wait_for_complete(action)

    # Assert the result is correct
    assert result is not None
    assert isinstance(result, CreateClusterActionResult)
    assert result.session_id == SESSION_FIXTURE_DATA.id
    assert result.result == CREATE_CLUSTER_MOCK

    # Verify the mock was called correctly
    mock_create_cluster_rpc.assert_called_once()
