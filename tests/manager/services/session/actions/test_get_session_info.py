from decimal import Decimal
from typing import cast
from unittest.mock import AsyncMock

import pytest

from ai.backend.common.types import AccessKey
from ai.backend.manager.models.session import SessionStatus
from ai.backend.manager.services.session.actions.get_session_info import (
    GetSessionInfoAction,
    GetSessionInfoActionResult,
)
from ai.backend.manager.services.session.processors import SessionProcessors
from ai.backend.manager.services.session.types import LegacySessionInfo

from ...test_utils import TestScenario
from ..fixtures import (
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
def mock_get_session_info_service(mocker):
    mock = mocker.patch(
        "ai.backend.manager.services.session.service.SessionService.get_session_info",
        new_callable=AsyncMock,
    )
    mock.return_value = GetSessionInfoActionResult(
        session_info=EXPECTED_RESULT,
        session_data=SESSION_FIXTURE_DATA,
    )
    return mock


@pytest.mark.parametrize(
    "test_scenario",
    [
        TestScenario.success(
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
            "sessions": [SESSION_FIXTURE_DICT],
            "kernels": [KERNEL_FIXTURE_DICT],
        }
    ],
)
async def test_get_session_info(
    mock_get_session_info_service,
    processors: SessionProcessors,
    test_scenario: TestScenario[GetSessionInfoAction, GetSessionInfoActionResult],
):
    await test_scenario.test(processors.get_session_info.wait_for_complete)
