from typing import cast
from unittest.mock import AsyncMock

import pytest

from ai.backend.common.types import AccessKey
from ai.backend.manager.services.session.actions.start_service import (
    StartServiceAction,
    StartServiceActionResult,
)
from ai.backend.manager.services.session.processors import SessionProcessors

from ...test_utils import TestScenario
from ..fixtures import (
    KERNEL_FIXTURE_DICT,
    SESSION_FIXTURE_DATA,
    SESSION_FIXTURE_DICT,
)


@pytest.fixture
def mock_start_service_rpc(mocker, mock_agent_response_result):
    mock = mocker.patch(
        "ai.backend.manager.services.session.service.SessionService.start_service",
        new_callable=AsyncMock,
    )
    mock.return_value = StartServiceActionResult(
        result=mock_agent_response_result,
        session_data=SESSION_FIXTURE_DATA,
        token="test_token",
        wsproxy_addr="localhost:8080",
    )
    return mock


START_SERVICE_MOCK = {"started": True, "port": 8080}


@pytest.mark.parametrize(
    ("test_scenario", "mock_agent_response_result"),
    [
        (
            TestScenario.success(
                "Start service",
                StartServiceAction(
                    session_name=cast(str, SESSION_FIXTURE_DATA.name),
                    access_key=cast(AccessKey, SESSION_FIXTURE_DATA.access_key),
                    service="test_service",
                    login_session_token="test_token",
                    port=8080,
                    arguments=None,
                    envs=None,
                ),
                StartServiceActionResult(
                    result=START_SERVICE_MOCK,
                    session_data=SESSION_FIXTURE_DATA,
                    token="test_token",
                    wsproxy_addr="localhost:8080",
                ),
            ),
            START_SERVICE_MOCK,
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
async def test_start_service(
    mock_start_service_rpc,
    processors: SessionProcessors,
    test_scenario: TestScenario[StartServiceAction, StartServiceActionResult],
):
    await test_scenario.test(processors.start_service.wait_for_complete)
