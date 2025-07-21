from dataclasses import replace

import pytest

from ai.backend.manager.services.session.actions.modify_session import (
    ModifySessionAction,
    ModifySessionActionResult,
    SessionModifier,
)
from ai.backend.manager.services.session.processors import SessionProcessors
from ai.backend.manager.types import OptionalState

from ...test_utils import TestScenario
from ..fixtures import KERNEL_FIXTURE_DICT, SESSION_FIXTURE_DATA, SESSION_FIXTURE_DICT


@pytest.mark.parametrize(
    "test_scenario",
    [
        TestScenario.success(
            "Update name, priority",
            ModifySessionAction(
                session_id=SESSION_FIXTURE_DATA.id,
                modifier=SessionModifier(
                    name=OptionalState.update("new_name"),
                    priority=OptionalState.update(100),
                ),
            ),
            ModifySessionActionResult(
                session_data=replace(SESSION_FIXTURE_DATA, name="new_name", priority=100)
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
async def test_modify_session(
    processors: SessionProcessors,
    test_scenario: TestScenario[ModifySessionAction, ModifySessionActionResult],
):
    await test_scenario.test(processors.modify_session.wait_for_complete)
