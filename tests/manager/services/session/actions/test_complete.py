from typing import cast
from unittest.mock import AsyncMock

import pytest

from ai.backend.common.dto.agent.response import CodeCompletionResp, CodeCompletionResult
from ai.backend.common.types import AccessKey
from ai.backend.manager.services.session.actions.complete import (
    CompleteAction,
    CompleteActionResult,
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
def mock_agent_complete_session_rpc(mocker, mock_agent_response_result):
    mock = mocker.patch(
        "ai.backend.manager.registry.AgentRegistry.complete_session",
        new_callable=AsyncMock,
    )
    mock.return_value = mock_agent_response_result
    return mock


COMPLETE_SESSION_MOCK = CodeCompletionResp(
    result=CodeCompletionResult(
        status="finished",
        error=None,
        suggestions=["test_completion"],
    )
)


@pytest.mark.parametrize(
    ("test_scenario", "mock_agent_response_result"),
    [
        (
            TestScenario.success(
                "Complete session",
                CompleteAction(
                    session_name=cast(str, SESSION_FIXTURE_DATA.name),
                    owner_access_key=cast(AccessKey, SESSION_FIXTURE_DATA.access_key),
                    code="print('Hello')",
                    options=None,
                ),
                CompleteActionResult(
                    result=COMPLETE_SESSION_MOCK,
                    session_row=SESSION_ROW_FIXTURE,
                ),
            ),
            COMPLETE_SESSION_MOCK,
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
async def test_complete_session(
    mock_agent_complete_session_rpc,
    processors: SessionProcessors,
    test_scenario: TestScenario[CompleteAction, CompleteActionResult],
):
    await test_scenario.test(processors.complete.wait_for_complete)
