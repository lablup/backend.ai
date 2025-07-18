from typing import cast
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.types import AccessKey, ClusterMode, SessionTypes
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.services.session.actions.create_from_params import (
    CreateFromParamsAction,
    CreateFromParamsActionParams,
    CreateFromParamsActionResult,
)
from ai.backend.manager.services.session.processors import SessionProcessors

from ...test_utils import TestScenario
from ..fixtures import (
    KERNEL_FIXTURE_DICT,
    SESSION_FIXTURE_DATA,
    SESSION_FIXTURE_DICT,
)


@pytest.fixture
def mock_create_from_params_rpc(mocker, mock_agent_response_result):
    mock = mocker.patch(
        "ai.backend.manager.registry.AgentRegistry.create_session",
        new_callable=AsyncMock,
    )
    mock.return_value = mock_agent_response_result
    return mock


@pytest.fixture
def mock_resolve_image(mocker):
    mock_image_row = MagicMock()
    mock_image_row.id = "test_image_id"
    mock_image_row.canonical = "python:3.9"
    mock_image_row.architecture = "x86_64"

    mock = mocker.patch(
        "ai.backend.manager.repositories.session.repository.SessionRepository.resolve_image",
        new_callable=AsyncMock,
        return_value=mock_image_row,
    )
    return mock


@pytest.fixture
def mock_session_service_create_from_params(mocker, mock_agent_response_result):
    # Mock additional repository methods needed for session creation
    mocker.patch(
        "ai.backend.manager.repositories.session.repository.SessionRepository.query_userinfo",
        new_callable=AsyncMock,
        return_value=("user_info", SESSION_FIXTURE_DATA.group_id, "resource_policy"),
    )

    # Mock AgentRegistry.create_session to return the expected result
    mocker.patch(
        "ai.backend.manager.registry.AgentRegistry.create_session",
        new_callable=AsyncMock,
        return_value=mock_agent_response_result,
    )

    return None


CREATE_FROM_PARAMS_MOCK = {"sessionId": str(SESSION_FIXTURE_DATA.id)}


CREATE_FROM_PARAMS_ACTION = CreateFromParamsAction(
    params=CreateFromParamsActionParams(
        session_name=cast(str, SESSION_FIXTURE_DATA.name),
        image="python:3.9",
        architecture="x86_64",
        session_type=SessionTypes.INTERACTIVE,
        group_name="default",
        domain_name="default",
        cluster_size=1,
        cluster_mode=ClusterMode.SINGLE_NODE,
        config={},
        tag="latest",
        priority=0,
        owner_access_key=cast(AccessKey, SESSION_FIXTURE_DATA.access_key),
        enqueue_only=False,
        max_wait_seconds=0,
        starts_at=None,
        reuse_if_exists=False,
        startup_command=None,
        batch_timeout=None,
        bootstrap_script=None,
        dependencies=None,
        callback_url=None,
    ),
    user_id=SESSION_FIXTURE_DATA.user_uuid,
    user_role=UserRole.USER,
    sudo_session_enabled=False,
    requester_access_key=cast(AccessKey, SESSION_FIXTURE_DATA.access_key),
    keypair_resource_policy=None,
)


@pytest.mark.parametrize(
    ("test_scenario", "mock_agent_response_result"),
    [
        (
            TestScenario.success(
                "Create session from params",
                CREATE_FROM_PARAMS_ACTION,
                CreateFromParamsActionResult(
                    session_id=SESSION_FIXTURE_DATA.id,
                    result=CREATE_FROM_PARAMS_MOCK,
                ),
            ),
            CREATE_FROM_PARAMS_MOCK,
        ),
        (
            TestScenario.failure(
                "Create session with unknown image",
                CreateFromParamsAction(
                    params=CreateFromParamsActionParams(
                        session_name="test-session",
                        image="non-existent:latest",
                        architecture="x86_64",
                        session_type=SessionTypes.INTERACTIVE,
                        group_name="default",
                        domain_name="default",
                        cluster_size=1,
                        cluster_mode=ClusterMode.SINGLE_NODE,
                        config={},
                        tag="latest",
                        priority=0,
                        owner_access_key=cast(AccessKey, SESSION_FIXTURE_DATA.access_key),
                        enqueue_only=False,
                        max_wait_seconds=0,
                        starts_at=None,
                        reuse_if_exists=False,
                        startup_command=None,
                        batch_timeout=None,
                        bootstrap_script=None,
                        dependencies=None,
                        callback_url=None,
                    ),
                    user_id=SESSION_FIXTURE_DATA.user_uuid,
                    user_role=UserRole.USER,
                    sudo_session_enabled=False,
                    requester_access_key=cast(AccessKey, SESSION_FIXTURE_DATA.access_key),
                    keypair_resource_policy=None,
                ),
                Exception,  # Will be mocked to raise an exception
            ),
            None,
        ),
        (
            TestScenario.success(
                "Create session with environment variables",
                CreateFromParamsAction(
                    params=CreateFromParamsActionParams(
                        session_name="env-test-session",
                        image="python:3.9",
                        architecture="x86_64",
                        session_type=SessionTypes.INTERACTIVE,
                        group_name="default",
                        domain_name="default",
                        cluster_size=1,
                        cluster_mode=ClusterMode.SINGLE_NODE,
                        config={
                            "environ": {
                                "CUDA_VISIBLE_DEVICES": "0",
                                "PYTHONPATH": "/app",
                                "CUSTOM_VAR": "test_value",
                            }
                        },
                        tag="latest",
                        priority=0,
                        owner_access_key=cast(AccessKey, SESSION_FIXTURE_DATA.access_key),
                        enqueue_only=False,
                        max_wait_seconds=0,
                        starts_at=None,
                        reuse_if_exists=False,
                        startup_command=None,
                        batch_timeout=None,
                        bootstrap_script=None,
                        dependencies=None,
                        callback_url=None,
                    ),
                    user_id=SESSION_FIXTURE_DATA.user_uuid,
                    user_role=UserRole.USER,
                    sudo_session_enabled=False,
                    requester_access_key=cast(AccessKey, SESSION_FIXTURE_DATA.access_key),
                    keypair_resource_policy=None,
                ),
                CreateFromParamsActionResult(
                    session_id=SESSION_FIXTURE_DATA.id,
                    result=CREATE_FROM_PARAMS_MOCK,
                ),
            ),
            CREATE_FROM_PARAMS_MOCK,
        ),
        (
            TestScenario.success(
                "Create session with bootstrap script",
                CreateFromParamsAction(
                    params=CreateFromParamsActionParams(
                        session_name="bootstrap-test-session",
                        image="python:3.9",
                        architecture="x86_64",
                        session_type=SessionTypes.INTERACTIVE,
                        group_name="default",
                        domain_name="default",
                        cluster_size=1,
                        cluster_mode=ClusterMode.SINGLE_NODE,
                        config={},
                        tag="latest",
                        priority=0,
                        owner_access_key=cast(AccessKey, SESSION_FIXTURE_DATA.access_key),
                        enqueue_only=False,
                        max_wait_seconds=0,
                        starts_at=None,
                        reuse_if_exists=False,
                        startup_command=None,
                        batch_timeout=None,
                        bootstrap_script="cGlwIGluc3RhbGwgLXIgcmVxdWlyZW1lbnRzLnR4dApweXRob24gc2V0dXAucHk=",  # base64 encoded
                        dependencies=None,
                        callback_url=None,
                    ),
                    user_id=SESSION_FIXTURE_DATA.user_uuid,
                    user_role=UserRole.USER,
                    sudo_session_enabled=False,
                    requester_access_key=cast(AccessKey, SESSION_FIXTURE_DATA.access_key),
                    keypair_resource_policy=None,
                ),
                CreateFromParamsActionResult(
                    session_id=SESSION_FIXTURE_DATA.id,
                    result=CREATE_FROM_PARAMS_MOCK,
                ),
            ),
            CREATE_FROM_PARAMS_MOCK,
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
async def test_create_from_params(
    mock_session_service_create_from_params,
    mock_resolve_image,
    processors: SessionProcessors,
    test_scenario: TestScenario[CreateFromParamsAction, CreateFromParamsActionResult],
):
    # Execute the actual service
    result = await processors.create_from_params.wait_for_complete(test_scenario.input)

    # Verify the result
    assert result is not None
    assert isinstance(result, CreateFromParamsActionResult)
    assert result.session_id is not None
    assert result.result is not None
    assert "sessionId" in result.result

    # Verify the mocks were called
    mock_resolve_image.assert_called_once()
