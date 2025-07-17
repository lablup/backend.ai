from typing import cast
from unittest.mock import AsyncMock

import pytest

from ai.backend.common.types import AccessKey
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.services.session.actions.destory_session import (
    DestroySessionAction,
    DestroySessionActionResult,
)
from ai.backend.manager.services.session.processors import SessionProcessors

from ...test_utils import TestScenario
from ..fixtures import (
    KERNEL_FIXTURE_DICT,
    SESSION_FIXTURE_DATA,
    SESSION_FIXTURE_DICT,
    SESSION_ROW_FIXTURE,
)


@pytest.fixture
def mock_destroy_session_rpc(mocker, mock_agent_response_result):
    mock = mocker.patch(
        "ai.backend.manager.registry.AgentRegistry.destroy_session",
        new_callable=AsyncMock,
    )
    mock.return_value = mock_agent_response_result
    return mock


DESTROY_SESSION_MOCK = {"destroyed": True}


@pytest.mark.parametrize(
    ("test_scenario", "mock_agent_response_result"),
    [
        (
            TestScenario.success(
                "Destroy session",
                DestroySessionAction(
                    user_role=UserRole.USER,
                    session_name=cast(str, SESSION_FIXTURE_DATA.name),
                    forced=False,
                    recursive=False,
                    owner_access_key=cast(AccessKey, SESSION_FIXTURE_DATA.access_key),
                ),
                DestroySessionActionResult(
                    destroyed_sessions=[SESSION_ROW_FIXTURE],
                    result=DESTROY_SESSION_MOCK,
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
            "sessions": [SESSION_FIXTURE_DICT],
            "kernels": [KERNEL_FIXTURE_DICT],
        }
    ],
)
async def test_destroy_session(
    mock_destroy_session_rpc,
    processors: SessionProcessors,
    test_scenario: TestScenario[DestroySessionAction, DestroySessionActionResult],
):
    await test_scenario.test(processors.destroy_session.wait_for_complete)
