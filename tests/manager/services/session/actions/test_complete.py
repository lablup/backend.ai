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
)


@pytest.fixture
def mock_agent_complete_session_rpc(mocker, mock_agent_response_result):
    mock = mocker.patch(
        "ai.backend.manager.registry.AgentRegistry.get_completions",
        new_callable=AsyncMock,
    )
    mock.return_value = mock_agent_response_result
    return mock


@pytest.fixture
def mock_session_service_complete(mocker, mock_agent_response_result):
    mock = mocker.patch(
        "ai.backend.manager.services.session.service.SessionService.complete",
        new_callable=AsyncMock,
    )
    mock.return_value = CompleteActionResult(
        session_data=SESSION_FIXTURE_DATA,
        result=mock_agent_response_result,
    )
    return mock


COMPLETE_SESSION_MOCK = CodeCompletionResp(
    result=CodeCompletionResult(
        status="finished",
        error=None,
        suggestions=["test_completion"],
    )
)


COMPLETE_ACTION = CompleteAction(
    session_name=cast(str, SESSION_FIXTURE_DATA.name),
    owner_access_key=cast(AccessKey, SESSION_FIXTURE_DATA.access_key),
    code="print('Hello')",
    options=None,
)


@pytest.mark.parametrize(
    ("test_scenario", "mock_agent_response_result"),
    [
        (
            TestScenario.success(
                "Complete session",
                COMPLETE_ACTION,
                CompleteActionResult(
                    session_data=SESSION_FIXTURE_DATA,
                    result=COMPLETE_SESSION_MOCK,
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
    mock_session_service_complete,
    processors: SessionProcessors,
    test_scenario: TestScenario[CompleteAction, CompleteActionResult],
):
    await test_scenario.test(processors.complete.wait_for_complete)
