from typing import cast
from unittest.mock import AsyncMock

import pytest

from ai.backend.common.types import AccessKey
from ai.backend.manager.services.session.actions.get_dependency_graph import (
    GetDependencyGraphAction,
    GetDependencyGraphActionResult,
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
def mock_get_dependency_graph_rpc(mocker, mock_agent_response_result):
    mock = mocker.patch(
        "ai.backend.manager.registry.AgentRegistry.get_dependency_graph",
        new_callable=AsyncMock,
    )
    mock.return_value = mock_agent_response_result
    return mock


GET_DEPENDENCY_GRAPH_MOCK = {
    "nodes": [{"id": "node1", "type": "function"}],
    "edges": [{"from": "node1", "to": "node2"}],
}


@pytest.mark.parametrize(
    ("test_scenario", "mock_agent_response_result"),
    [
        (
            TestScenario.success(
                "Get dependency graph",
                GetDependencyGraphAction(
                    root_session_name=cast(str, SESSION_FIXTURE_DATA.name),
                    owner_access_key=cast(AccessKey, SESSION_FIXTURE_DATA.access_key),
                ),
                GetDependencyGraphActionResult(
                    result=GET_DEPENDENCY_GRAPH_MOCK,
                    session_row=SESSION_ROW_FIXTURE,
                ),
            ),
            GET_DEPENDENCY_GRAPH_MOCK,
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
async def test_get_dependency_graph(
    mock_get_dependency_graph_rpc,
    processors: SessionProcessors,
    test_scenario: TestScenario[GetDependencyGraphAction, GetDependencyGraphActionResult],
):
    await test_scenario.test(processors.get_dependency_graph.wait_for_complete)
