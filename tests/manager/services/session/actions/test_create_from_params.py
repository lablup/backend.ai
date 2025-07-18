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
    mock = mocker.patch(
        "ai.backend.manager.services.session.service.SessionService.create_from_params",
        new_callable=AsyncMock,
    )
    mock.return_value = CreateFromParamsActionResult(
        session_id=SESSION_FIXTURE_DATA.id,
        result=mock_agent_response_result,
    )
    return mock


CREATE_FROM_PARAMS_MOCK = {"sessionId": "test_session_123"}


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
    await test_scenario.test(processors.create_from_params.wait_for_complete)
