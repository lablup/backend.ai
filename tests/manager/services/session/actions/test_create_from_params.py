from typing import cast
from unittest.mock import AsyncMock

import pytest

from ai.backend.common.types import AccessKey, ClusterMode, SessionTypes
from ai.backend.manager.errors.image import ImageNotFound
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.services.session.actions.create_from_params import (
    CreateFromParamsAction,
    CreateFromParamsActionParams,
    CreateFromParamsActionResult,
)
from ai.backend.manager.services.session.processors import SessionProcessors

from ...fixtures import (
    IMAGE_ALIAS_DICT,
    IMAGE_FIXTURE_DICT,
)
from ...utils import ScenarioBase
from ..fixtures import (
    AGENT_FIXTURE_DICT,
    GROUP_FIXTURE_DATA,
    GROUP_USER_ASSOCIATION_DATA,
    KERNEL_FIXTURE_DICT,
    SESSION_FIXTURE_DATA,
    SESSION_FIXTURE_DICT,
    USER_FIXTURE_DATA,
)


@pytest.fixture
def mock_create_from_params_rpc(mocker):
    mock_create_session = mocker.patch(
        "ai.backend.manager.registry.AgentRegistry.create_session",
        new_callable=AsyncMock,
    )

    return {
        "create_session": mock_create_session,
    }


CREATE_FROM_PARAMS_MOCK = {"sessionId": str(SESSION_FIXTURE_DATA.id)}


CREATE_FROM_PARAMS_ACTION = CreateFromParamsAction(
    params=CreateFromParamsActionParams(
        session_name=cast(str, SESSION_FIXTURE_DATA.name),
        image="python",  # Use the actual fixture image alias
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
    "test_scenario",
    [
        ScenarioBase.success(
            "Create session from params",
            CREATE_FROM_PARAMS_ACTION,
            CreateFromParamsActionResult(
                session_id=SESSION_FIXTURE_DATA.id,
                result=CREATE_FROM_PARAMS_MOCK,
            ),
        ),
        ScenarioBase.failure(
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
            ImageNotFound,  # Actual error when image is not found in database
        ),
        ScenarioBase.success(
            "Create session with environment variables",
            CreateFromParamsAction(
                params=CreateFromParamsActionParams(
                    session_name="env-test-session",
                    image="python",  # Use the actual fixture image alias
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
        ScenarioBase.success(
            "Create session with bootstrap script",
            CreateFromParamsAction(
                params=CreateFromParamsActionParams(
                    session_name="bootstrap-test-session",
                    image="python",  # Use the actual fixture image alias
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
    ],
)
@pytest.mark.parametrize(
    "extra_fixtures",
    [
        {
            "agents": [AGENT_FIXTURE_DICT],
            "sessions": [SESSION_FIXTURE_DICT],
            "kernels": [KERNEL_FIXTURE_DICT],
            "users": [USER_FIXTURE_DATA],
            "groups": [GROUP_FIXTURE_DATA],
            "association_groups_users": [GROUP_USER_ASSOCIATION_DATA],
            "images": [IMAGE_FIXTURE_DICT],
            "image_aliases": [IMAGE_ALIAS_DICT],
        }
    ],
)
async def test_create_from_params(
    mock_create_from_params_rpc,
    processors: SessionProcessors,
    test_scenario: ScenarioBase[CreateFromParamsAction, CreateFromParamsActionResult],
    session_repository,
):
    # Set up the mock return value for create_session
    if test_scenario.expected_exception is None:
        mock_create_from_params_rpc["create_session"].return_value = CREATE_FROM_PARAMS_MOCK

    # Use the test scenario's built-in test method that handles both success and failure cases
    await test_scenario.test(processors.create_from_params.wait_for_complete)

    # Verify the mocks were called (only for successful cases)
    if test_scenario.expected_exception is None:
        mock_create_from_params_rpc["create_session"].assert_called_once()

    # TODO: Verify the session was created in the database
