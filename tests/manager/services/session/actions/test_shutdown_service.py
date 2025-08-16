from typing import cast
from unittest.mock import AsyncMock

import pytest

from ai.backend.common.types import AccessKey
from ai.backend.manager.services.session.actions.shutdown_service import (
    ShutdownServiceAction,
    ShutdownServiceActionResult,
)
from ai.backend.manager.services.session.processors import SessionProcessors

from ...utils import ScenarioBase
from ..fixtures import (
    KERNEL_FIXTURE_DICT,
    SESSION_FIXTURE_DATA,
    SESSION_FIXTURE_DICT,
)


@pytest.fixture
def mock_shutdown_service_rpc(mocker, mock_agent_response_result):
    mocker.patch(
        "ai.backend.manager.registry.AgentRegistry.shutdown_service",
        new_callable=AsyncMock,
    )

    return mock_agent_response_result


SHUTDOWN_SERVICE_MOCK = None


@pytest.mark.parametrize(
    ("test_scenario", "mock_agent_response_result"),
    [
        (
            ScenarioBase.success(
                "Shutdown service",
                ShutdownServiceAction(
                    session_name=cast(str, SESSION_FIXTURE_DATA.name),
                    owner_access_key=cast(AccessKey, SESSION_FIXTURE_DATA.access_key),
                    service_name="test_service",
                ),
                ShutdownServiceActionResult(
                    result=SHUTDOWN_SERVICE_MOCK,
                    session_data=SESSION_FIXTURE_DATA,
                ),
            ),
            SHUTDOWN_SERVICE_MOCK,
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
async def test_shutdown_service(
    mock_shutdown_service_rpc,
    processors: SessionProcessors,
    test_scenario: ScenarioBase[ShutdownServiceAction, ShutdownServiceActionResult],
):
    # Expected result will use the session data from the database fixture
    assert test_scenario.expected is not None
    test_scenario.expected.session_data = SESSION_FIXTURE_DATA
    await test_scenario.test(processors.shutdown_service.wait_for_complete)
