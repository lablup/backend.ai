from typing import cast
from unittest.mock import AsyncMock

import pytest

from ai.backend.common.types import AccessKey
from ai.backend.manager.services.session.actions.get_direct_access_info import (
    GetDirectAccessInfoAction,
    GetDirectAccessInfoActionResult,
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
def mock_get_direct_access_info_rpc(mocker, mock_agent_response_result):
    mock = mocker.patch(
        "ai.backend.manager.registry.AgentRegistry.get_direct_access_info",
        new_callable=AsyncMock,
    )
    mock.return_value = mock_agent_response_result
    return mock


GET_DIRECT_ACCESS_INFO_MOCK = {
    "public_host": "example.com",
    "port": 8080,
    "token": "test_token_123",
}


@pytest.mark.parametrize(
    ("test_scenario", "mock_agent_response_result"),
    [
        (
            TestScenario.success(
                "Get direct access info",
                GetDirectAccessInfoAction(
                    session_name=cast(str, SESSION_FIXTURE_DATA.name),
                    owner_access_key=cast(AccessKey, SESSION_FIXTURE_DATA.access_key),
                ),
                GetDirectAccessInfoActionResult(
                    result=GET_DIRECT_ACCESS_INFO_MOCK,
                    session_row=SESSION_ROW_FIXTURE,
                ),
            ),
            GET_DIRECT_ACCESS_INFO_MOCK,
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
async def test_get_direct_access_info(
    mock_get_direct_access_info_rpc,
    processors: SessionProcessors,
    test_scenario: TestScenario[GetDirectAccessInfoAction, GetDirectAccessInfoActionResult],
):
    await test_scenario.test(processors.get_direct_access_info.wait_for_complete)
