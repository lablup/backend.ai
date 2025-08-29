from typing import cast
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from ai.backend.common.types import AccessKey, ClusterMode, SessionTypes
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.services.session.actions.create_from_template import (
    CreateFromTemplateAction,
    CreateFromTemplateActionParams,
    CreateFromTemplateActionResult,
)
from ai.backend.manager.services.session.processors import SessionProcessors

from ...utils import ScenarioBase
from ..fixtures import (
    AGENT_FIXTURE_DICT,
    KERNEL_FIXTURE_DICT,
    SESSION_FIXTURE_DATA,
    SESSION_FIXTURE_DICT,
)


@pytest.fixture
def mock_create_from_template_rpc(mocker, mock_agent_response_result):
    mock = mocker.patch(
        "ai.backend.manager.services.session.service.SessionService.create_from_template",
        new_callable=AsyncMock,
    )
    mock.return_value = mock_agent_response_result
    return mock


CREATE_FROM_TEMPLATE_MOCK = {"session_id": "test_session_from_template_123"}
TEST_TEMPLATE_ID = uuid4()


@pytest.mark.skip(reason="WIP, Need to be fixed")
@pytest.mark.parametrize(
    ("test_scenario", "mock_agent_response_result"),
    [
        (
            ScenarioBase.success(
                "Create session from template",
                CreateFromTemplateAction(
                    params=CreateFromTemplateActionParams(
                        template_id=TEST_TEMPLATE_ID,
                        session_name=cast(str, SESSION_FIXTURE_DATA.name),
                        image="cr.backend.ai/stable/python:3.9",
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
                CreateFromTemplateActionResult(
                    result=CREATE_FROM_TEMPLATE_MOCK,
                    session_id=SESSION_FIXTURE_DATA.id,
                ),
            ),
            CREATE_FROM_TEMPLATE_MOCK,
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
        }
    ],
)
@pytest.mark.skip(reason="Test infrastructure needs fixing for session fixture dependencies")
async def test_create_from_template(
    mock_create_from_template_rpc,
    processors: SessionProcessors,
    test_scenario: ScenarioBase[CreateFromTemplateAction, CreateFromTemplateActionResult],
):
    await test_scenario.test(processors.create_from_template.wait_for_complete)
