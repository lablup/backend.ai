from dataclasses import replace
from typing import cast

import pytest

from ai.backend.common.exception import InvalidAPIParameters
from ai.backend.common.types import AccessKey
from ai.backend.manager.services.session.actions.rename_session import (
    RenameSessionAction,
    RenameSessionActionResult,
)
from ai.backend.manager.services.session.processors import SessionProcessors

from ...utils import ScenarioBase
from ..fixtures import (
    AGENT_FIXTURE_DICT,
    KERNEL_FIXTURE_DICT,
    PENDING_SESSION_FIXTURE_DATA,
    PENDING_SESSION_FIXTURE_DICT,
    SESSION_FIXTURE_DATA,
    SESSION_FIXTURE_DICT,
)


@pytest.mark.parametrize(
    "test_scenario",
    [
        ScenarioBase.success(
            "Rename session",
            RenameSessionAction(
                session_name=cast(str, SESSION_FIXTURE_DATA.name),
                new_name="new_name",
                owner_access_key=cast(AccessKey, SESSION_FIXTURE_DATA.access_key),
            ),
            RenameSessionActionResult(session_data=replace(SESSION_FIXTURE_DATA, name="new_name")),
        ),
        ScenarioBase.failure(
            "Cannot rename not running session",
            RenameSessionAction(
                session_name=cast(str, PENDING_SESSION_FIXTURE_DATA.name),
                new_name="new_name",
                owner_access_key=cast(AccessKey, PENDING_SESSION_FIXTURE_DATA.access_key),
            ),
            InvalidAPIParameters,
        ),
    ],
)
@pytest.mark.parametrize(
    "extra_fixtures",
    [
        {
            "agents": [AGENT_FIXTURE_DICT],
            "sessions": [SESSION_FIXTURE_DICT, PENDING_SESSION_FIXTURE_DICT],
            "kernels": [KERNEL_FIXTURE_DICT],
        }
    ],
)
async def test_rename_session(
    processors: SessionProcessors,
    test_scenario: ScenarioBase[RenameSessionAction, RenameSessionActionResult],
):
    await test_scenario.test(processors.rename_session.wait_for_complete)
