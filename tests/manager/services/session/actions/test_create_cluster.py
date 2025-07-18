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
    KERNEL_FIXTURE_DICT,
    SESSION_FIXTURE_DATA,
    SESSION_FIXTURE_DICT,
)


@pytest.fixture
def mock_create_cluster_service(mocker):
    mock = mocker.patch(
        "ai.backend.manager.services.session.service.SessionService.create_cluster",
        new_callable=AsyncMock,
    )
    mock.return_value = CreateClusterActionResult(
        session_id=SESSION_FIXTURE_DATA.id,
        result=CREATE_CLUSTER_MOCK,
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
    mock_create_cluster_service,
    processors: SessionProcessors,
):
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
    mock_create_cluster_service.assert_called_once()
