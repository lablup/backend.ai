from typing import cast
from unittest.mock import AsyncMock
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
    GROUP_FIXTURE_DATA,
    GROUP_USER_ASSOCIATION_DATA,
    KERNEL_FIXTURE_DICT,
    SESSION_FIXTURE_DATA,
    SESSION_FIXTURE_DICT,
    USER_FIXTURE_DATA,
)


@pytest.fixture
def mock_create_cluster_dependencies(mocker):
    # Mock only the AgentRegistry create_cluster method (external service)
    mock_create_cluster = mocker.patch(
        "ai.backend.manager.registry.AgentRegistry.create_cluster",
        new_callable=AsyncMock,
    )
    mock_create_cluster.return_value = CREATE_CLUSTER_MOCK

    # Mock query_userinfo to return consistent results
    from ai.backend.manager.repositories.session.repository import SessionRepository

    mock_query_userinfo = mocker.patch.object(
        SessionRepository,
        "query_userinfo",
        new_callable=AsyncMock,
    )
    mock_query_userinfo.return_value = (
        SESSION_FIXTURE_DATA.user_uuid,
        SESSION_FIXTURE_DATA.group_id,
        {"cpu": 4, "memory": "8g"},  # Mock resource policy
    )

    return {
        "create_cluster": mock_create_cluster,
        "query_userinfo": mock_query_userinfo,
    }


CREATE_CLUSTER_MOCK = {"cluster_id": "test_cluster_123", "kernelId": SESSION_FIXTURE_DATA.id}
TEST_TEMPLATE_ID = uuid4()


# Test template-based cluster creation
@pytest.mark.parametrize(
    "extra_fixtures",
    [
        {
            "sessions": [SESSION_FIXTURE_DICT],
            "kernels": [KERNEL_FIXTURE_DICT],
            "users": [USER_FIXTURE_DATA],
            "groups": [GROUP_FIXTURE_DATA],
            "association_groups_users": [GROUP_USER_ASSOCIATION_DATA],
            "session_templates": [
                {
                    "id": TEST_TEMPLATE_ID,
                    "name": "test_template",
                    "template": {"spec": {"kernel": {"image": "python:3.9"}}},
                    "domain_name": SESSION_FIXTURE_DATA.domain_name,
                    "group_id": SESSION_FIXTURE_DATA.group_id,
                    "user_uuid": SESSION_FIXTURE_DATA.user_uuid,
                    "is_active": True,
                    "created_at": "2024-01-01T00:00:00Z",
                }
            ],
        }
    ],
)
async def test_create_cluster_with_template(
    mock_create_cluster_dependencies,
    processors: SessionProcessors,
    session_repository,
):
    # Create the action using template
    action = CreateClusterAction(
        session_name=cast(str, SESSION_FIXTURE_DATA.name),
        user_id=SESSION_FIXTURE_DATA.user_uuid,
        user_role=UserRole.USER,
        sudo_session_enabled=False,
        template_id=TEST_TEMPLATE_ID,
        session_type=SessionTypes.INTERACTIVE,
        group_name="test_group",
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

    # Verify the mocks were called
    mock_create_cluster_dependencies["create_cluster"].assert_called_once()


# Test different template scenarios
@pytest.mark.parametrize(
    "extra_fixtures",
    [
        {
            "sessions": [SESSION_FIXTURE_DICT],
            "kernels": [KERNEL_FIXTURE_DICT],
            "users": [USER_FIXTURE_DATA],
            "groups": [GROUP_FIXTURE_DATA],
            "association_groups_users": [GROUP_USER_ASSOCIATION_DATA],
            "session_templates": [
                {
                    "id": TEST_TEMPLATE_ID,
                    "name": "test_template_gpu",
                    "template": {
                        "spec": {
                            "kernel": {
                                "image": "python:3.9-gpu",
                                "resource_slots": {"cuda.shares": 1},
                            }
                        }
                    },
                    "domain_name": SESSION_FIXTURE_DATA.domain_name,
                    "group_id": SESSION_FIXTURE_DATA.group_id,
                    "user_uuid": SESSION_FIXTURE_DATA.user_uuid,
                    "is_active": True,
                    "created_at": "2024-01-01T00:00:00Z",
                }
            ],
        }
    ],
)
async def test_create_cluster_with_gpu_template(
    mock_create_cluster_dependencies,
    processors: SessionProcessors,
    session_repository,
):
    # Create the action using GPU template
    action = CreateClusterAction(
        session_name="gpu_test_session",
        user_id=SESSION_FIXTURE_DATA.user_uuid,
        user_role=UserRole.USER,
        sudo_session_enabled=False,
        template_id=TEST_TEMPLATE_ID,  # GPU template
        session_type=SessionTypes.INTERACTIVE,
        group_name="test_group",
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

    # Verify the mocks were called
    mock_create_cluster_dependencies["create_cluster"].assert_called_once()
