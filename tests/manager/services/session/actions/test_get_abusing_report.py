from typing import cast
from unittest.mock import AsyncMock

import pytest

from ai.backend.common.types import AbuseReport, AccessKey
from ai.backend.manager.services.session.actions.get_abusing_report import (
    GetAbusingReportAction,
    GetAbusingReportActionResult,
)
from ai.backend.manager.services.session.processors import SessionProcessors

from ...test_utils import TestScenario
from ..fixtures import (
    KERNEL_FIXTURE_DATA,
    KERNEL_FIXTURE_DICT,
    SESSION_FIXTURE_DATA,
    SESSION_FIXTURE_DICT,
)


@pytest.fixture
def mock_get_abusing_report_rpc(mocker, mock_agent_response_result):
    mock = mocker.patch(
        "ai.backend.manager.registry.AgentRegistry.get_abusing_report",
        new_callable=AsyncMock,
    )
    mock.return_value = mock_agent_response_result
    return mock


AGENT_GET_ABUSING_REPORT_RPC_RESP = AbuseReport(kernel=str(KERNEL_FIXTURE_DATA.id), abuse_report="")


@pytest.mark.parametrize(
    ("test_scenario", "mock_agent_response_result"),
    [
        (
            TestScenario.success(
                "Get abusing report",
                GetAbusingReportAction(
                    session_name=cast(str, SESSION_FIXTURE_DATA.name),
                    owner_access_key=cast(AccessKey, SESSION_FIXTURE_DATA.access_key),
                ),
                GetAbusingReportActionResult(
                    abuse_report=AGENT_GET_ABUSING_REPORT_RPC_RESP,
                    session_data=SESSION_FIXTURE_DATA,
                ),
            ),
            AGENT_GET_ABUSING_REPORT_RPC_RESP,
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
async def test_get_abusing_report(
    mock_get_abusing_report_rpc,
    processors: SessionProcessors,
    test_scenario: TestScenario[GetAbusingReportAction, GetAbusingReportActionResult],
):
    await test_scenario.test(processors.get_abusing_report.wait_for_complete)
