from typing import cast

import pytest

from ai.backend.common.types import AccessKey
from ai.backend.manager.data.session.types import SessionData
from ai.backend.manager.services.session.actions.get_direct_access_info import (
    GetDirectAccessInfoAction,
    GetDirectAccessInfoActionResult,
)
from ai.backend.manager.services.session.processors import SessionProcessors

from ...test_utils import TestScenario
from ..fixtures import (
    GROUP_FIXTURE_DATA,
    GROUP_USER_ASSOCIATION_DATA,
    KERNEL_FIXTURE_DICT,
    SESSION_FIXTURE_DATA,
    SESSION_FIXTURE_DICT,
    USER_FIXTURE_DATA,
)

GET_DIRECT_ACCESS_INFO_MOCK = {
    "kernel_role": "SYSTEM",
    "session_type": "SYSTEM",
    "public_host": "example.com",
    "sshd_ports": ["8023"],  # sftpd ports take precedence over sshd
}


@pytest.mark.parametrize(
    "test_scenario",
    [
        TestScenario.success(
            "Get direct access info",
            GetDirectAccessInfoAction(
                session_name=cast(str, SESSION_FIXTURE_DATA.name),
                owner_access_key=cast(AccessKey, SESSION_FIXTURE_DATA.access_key),
            ),
            GetDirectAccessInfoActionResult(
                result=GET_DIRECT_ACCESS_INFO_MOCK,
                session_data=SESSION_FIXTURE_DATA,  # Expected session data
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
            "users": [USER_FIXTURE_DATA],
            "groups": [GROUP_FIXTURE_DATA],
            "association_groups_users": [GROUP_USER_ASSOCIATION_DATA],
        }
    ],
)
async def test_get_direct_access_info(
    mock_session_repository_methods,
    processors: SessionProcessors,
    test_scenario: TestScenario[GetDirectAccessInfoAction, GetDirectAccessInfoActionResult],
    session_repository,
):
    # Execute the action
    result = await processors.get_direct_access_info.wait_for_complete(test_scenario.input)

    # Verify the result content matches expected
    assert result is not None
    assert isinstance(result, GetDirectAccessInfoActionResult)
    assert result.result == GET_DIRECT_ACCESS_INFO_MOCK

    # Verify session_data is properly returned (converted from SessionRow to SessionData)
    assert result.session_data is not None
    assert isinstance(result.session_data, SessionData)
    assert result.session_data.id == SESSION_FIXTURE_DATA.id
    assert result.session_data.name == SESSION_FIXTURE_DATA.name
    assert result.session_data.access_key == SESSION_FIXTURE_DATA.access_key
