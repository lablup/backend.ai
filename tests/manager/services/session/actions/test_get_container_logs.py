from typing import cast
from unittest.mock import AsyncMock

import pytest

from ai.backend.common.types import AccessKey, KernelId
from ai.backend.manager.services.session.actions.get_container_logs import (
    GetContainerLogsAction,
    GetContainerLogsActionResult,
)
from ai.backend.manager.services.session.processors import SessionProcessors

from ...utils import ScenarioBase
from ..fixtures import (
    AGENT_FIXTURE_DICT,
    KERNEL_FIXTURE_DATA,
    KERNEL_FIXTURE_DICT,
    SESSION_FIXTURE_DATA,
    SESSION_FIXTURE_DICT,
)


@pytest.fixture
def mock_agent_get_logs_from_agent_rpc(mocker, mock_agent_response_result):
    mock = mocker.patch(
        "ai.backend.manager.registry.AgentRegistry.get_logs_from_agent",
        new_callable=AsyncMock,
    )
    mock.return_value = mock_agent_response_result
    return mock


CONTAINER_LOGS_MOCK = "logs example"
AGENT_GET_CONTAINER_LOGS_RPC_RESP = {"result": {"logs": CONTAINER_LOGS_MOCK}}


@pytest.mark.parametrize(
    ("test_scenario", "mock_agent_response_result"),
    [
        (
            ScenarioBase.success(
                "Get container logs",
                GetContainerLogsAction(
                    session_name=cast(str, SESSION_FIXTURE_DATA.name),
                    owner_access_key=cast(AccessKey, SESSION_FIXTURE_DATA.access_key),
                    kernel_id=KernelId(KERNEL_FIXTURE_DATA.id),
                ),
                GetContainerLogsActionResult(
                    result=AGENT_GET_CONTAINER_LOGS_RPC_RESP,
                    session_data=SESSION_FIXTURE_DATA,
                ),
            ),
            CONTAINER_LOGS_MOCK,
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
async def test_get_container_logs_report(
    mock_agent_get_logs_from_agent_rpc,
    processors: SessionProcessors,
    test_scenario: ScenarioBase[GetContainerLogsAction, GetContainerLogsActionResult],
):
    await test_scenario.test(processors.get_container_logs.wait_for_complete)
