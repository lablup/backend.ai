from typing import cast
from unittest.mock import AsyncMock

import pytest

from ai.backend.common.types import AccessKey
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.services.session.actions.destroy_session import (
    DestroySessionAction,
    DestroySessionActionResult,
)
from ai.backend.manager.services.session.processors import SessionProcessors

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
def mock_agent_destroy_session_rpc(mocker, mock_agent_response_result):
    mock = mocker.patch(
        "ai.backend.manager.registry.AgentRegistry.destroy_session",
        new_callable=AsyncMock,
    )
    mock.return_value = mock_agent_response_result
    return mock


DESTROY_SESSION_MOCK = {"status": "cancelled"}
DESTROY_SESSION_RESPONSE_MOCK = {"stats": DESTROY_SESSION_MOCK}


@pytest.mark.parametrize(
    ("test_scenario", "mock_agent_response_result"),
    [
        (
            ScenarioBase.success(
                "Destroy session",
                DestroySessionAction(
                    user_role=UserRole.USER,
                    session_name=cast(str, SESSION_FIXTURE_DATA.name),
                    forced=False,
                    recursive=False,
                    owner_access_key=cast(AccessKey, SESSION_FIXTURE_DATA.access_key),
                ),
                DestroySessionActionResult(
                    result=DESTROY_SESSION_RESPONSE_MOCK,
                ),
            ),
            DESTROY_SESSION_MOCK,
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
        }
    ],
)
async def test_destroy_session(
    mock_agent_destroy_session_rpc,
    processors: SessionProcessors,
    test_scenario: ScenarioBase[DestroySessionAction, DestroySessionActionResult],
    session_repository,
):
    await test_scenario.test(processors.destroy_session.wait_for_complete)
