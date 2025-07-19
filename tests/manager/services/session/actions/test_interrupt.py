from typing import cast
from unittest.mock import AsyncMock

import pytest

from ai.backend.common.types import AccessKey
from ai.backend.manager.services.session.actions.interrupt_session import (
    InterruptSessionAction,
    InterruptSessionActionResult,
)
from ai.backend.manager.services.session.processors import SessionProcessors

from ...test_utils import TestScenario
from ..fixtures import (
    KERNEL_FIXTURE_DICT,
    SESSION_FIXTURE_DATA,
    SESSION_FIXTURE_DICT,
)


@pytest.fixture
def mock_interrupt_session_rpc(mocker, mock_agent_response_result):
    # Only mock agent registry methods - use real SessionRepository
    mocker.patch(
        "ai.backend.manager.registry.AgentRegistry.increment_session_usage",
        new_callable=AsyncMock,
    )
    mocker.patch(
        "ai.backend.manager.registry.AgentRegistry.interrupt_session",
        new_callable=AsyncMock,
    )

    return mock_agent_response_result


INTERRUPT_SESSION_MOCK = None


@pytest.mark.parametrize(
    ("test_scenario", "mock_agent_response_result"),
    [
        (
            TestScenario.success(
                "Interrupt session",
                InterruptSessionAction(
                    session_name=cast(str, SESSION_FIXTURE_DATA.name),
                    owner_access_key=cast(AccessKey, SESSION_FIXTURE_DATA.access_key),
                ),
                InterruptSessionActionResult(
                    result=INTERRUPT_SESSION_MOCK,
                    session_data=SESSION_FIXTURE_DATA,
                ),
            ),
            INTERRUPT_SESSION_MOCK,
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
async def test_interrupt_session(
    mock_interrupt_session_rpc,
    processors: SessionProcessors,
    test_scenario: TestScenario[InterruptSessionAction, InterruptSessionActionResult],
):
    # Expected result will use the session data from the database fixture
    assert test_scenario.expected is not None
    test_scenario.expected.session_data = SESSION_FIXTURE_DATA
    await test_scenario.test(processors.interrupt.wait_for_complete)
