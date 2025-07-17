from typing import cast
from unittest.mock import AsyncMock

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
        "ai.backend.manager.services.session.service.SessionService._create_from_params",
        new_callable=AsyncMock,
    )
    mock.return_value = mock_agent_response_result
    return mock


CREATE_FROM_PARAMS_MOCK = {"session_id": "test_session_123"}


@pytest.mark.parametrize(
    ("test_scenario", "mock_agent_response_result"),
    [
        (
            TestScenario.success(
                "Create session from params",
                CreateFromParamsAction(
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
                ),
                CreateFromParamsActionResult(
                    result=CREATE_FROM_PARAMS_MOCK,
                    session_id=SESSION_FIXTURE_DATA.id,
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
    mock_create_from_params_rpc,
    processors: SessionProcessors,
    test_scenario: TestScenario[CreateFromParamsAction, CreateFromParamsActionResult],
):
    await test_scenario.test(processors.create_from_params.wait_for_complete)
