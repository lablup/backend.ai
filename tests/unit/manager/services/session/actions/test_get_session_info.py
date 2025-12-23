from decimal import Decimal
from typing import cast
from unittest.mock import AsyncMock

import pytest

from ai.backend.common.types import AccessKey
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.services.session.actions.get_session_info import (
    GetSessionInfoAction,
    GetSessionInfoActionResult,
)
from ai.backend.manager.services.session.processors import SessionProcessors
from ai.backend.manager.services.session.types import LegacySessionInfo

from ...utils import ScenarioBase
from ..fixtures import (
    AGENT_FIXTURE_DICT,
    KERNEL_FIXTURE_DICT,
    KERNEL_ROW_FIXTURE,
    SESSION_FIXTURE_DATA,
    SESSION_FIXTURE_DICT,
)

EXPECTED_RESULT = LegacySessionInfo(
    age_ms=-1,  # doens't be compared
    domain_name=SESSION_FIXTURE_DATA.domain_name,
    group_id=SESSION_FIXTURE_DATA.group_id,
    user_id=SESSION_FIXTURE_DATA.user_uuid,
    lang=KERNEL_ROW_FIXTURE.image,
    image=KERNEL_ROW_FIXTURE.image,
    architecture=KERNEL_ROW_FIXTURE.architecture,
    registry=KERNEL_ROW_FIXTURE.registry,
    tag=SESSION_FIXTURE_DATA.tag,
    container_id=KERNEL_ROW_FIXTURE.container_id,
    occupied_slots=str({"cpu": Decimal("1"), "mem": Decimal("1024")}),
    occupying_slots=str({"cpu": Decimal("1"), "mem": Decimal("1024")}),
    requested_slots=str({"cpu": Decimal("1"), "mem": Decimal("1024")}),
    occupied_shares="{}",
    environ="{}",
    resource_opts="{'main1': {}}",
    status=SESSION_FIXTURE_DATA.status
    if isinstance(SESSION_FIXTURE_DATA.status, SessionStatus)
    else SessionStatus[SESSION_FIXTURE_DATA.status],
    status_info=None,
    status_data=None,
    creation_time=SESSION_FIXTURE_DATA.created_at,
    termination_time=None,
    num_queries_executed=0,
    last_stat=None,
    idle_checks={
        "session_lifetime": {
            "extra": None,
            "remaining": None,
            "remaining_time_type": "expire_after",
        },
    },
)


@pytest.fixture
def mock_increment_session_usage_rpc(mocker):
    mock_increment_usage = mocker.patch(
        "ai.backend.manager.registry.AgentRegistry.increment_session_usage",
        new_callable=AsyncMock,
    )
    return mock_increment_usage


@pytest.mark.parametrize(
    "test_scenario",
    [
        ScenarioBase.success(
            "Get session info",
            GetSessionInfoAction(
                session_name=cast(str, SESSION_FIXTURE_DATA.name),
                owner_access_key=cast(AccessKey, SESSION_FIXTURE_DATA.access_key),
            ),
            GetSessionInfoActionResult(
                session_info=EXPECTED_RESULT,
                session_data=SESSION_FIXTURE_DATA,
            ),
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
async def test_get_session_info(
    mock_increment_session_usage_rpc,
    processors: SessionProcessors,
    test_scenario: ScenarioBase[GetSessionInfoAction, GetSessionInfoActionResult],
):
    # Execute the actual service
    result = await processors.get_session_info.wait_for_complete(test_scenario.input)

    # Verify the result
    assert result is not None
    assert isinstance(result, GetSessionInfoActionResult)
    assert result.session_info is not None
    assert result.session_data is not None

    # Check key fields (ignoring age_ms which is calculated dynamically)
    assert result.session_info.domain_name == EXPECTED_RESULT.domain_name
    assert result.session_info.group_id == EXPECTED_RESULT.group_id
    assert result.session_info.user_id == EXPECTED_RESULT.user_id
    assert result.session_info.image == EXPECTED_RESULT.image
    assert result.session_info.status == EXPECTED_RESULT.status

    # Verify the mock was called
    mock_increment_session_usage_rpc.assert_called_once()
