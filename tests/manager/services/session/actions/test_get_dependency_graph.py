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
def mock_session_repository_methods(mocker, mock_agent_response_result):
    """Mock SessionRepository methods to return test data"""
    # Mock find_dependency_sessions to return the dependency graph with session_id
    mocker.patch(
        "ai.backend.manager.repositories.session.repository.SessionRepository.find_dependency_sessions",
        new_callable=AsyncMock,
        return_value={"session_id": [SESSION_ROW_FIXTURE.id], **mock_agent_response_result},
    )

    # Mock get_session_by_id to return the session with proper to_dataclass
    from unittest.mock import MagicMock

    mock_session = MagicMock()
    mock_session.to_dataclass.return_value = SESSION_FIXTURE_DATA
    mock_session.id = SESSION_FIXTURE_DATA.id

    mocker.patch(
        "ai.backend.manager.repositories.session.repository.SessionRepository.get_session_by_id",
        new_callable=AsyncMock,
        return_value=mock_session,
    )


GET_DEPENDENCY_GRAPH_BASE = {
    "nodes": [{"id": "node1", "type": "function"}],
    "edges": [{"from": "node1", "to": "node2"}],
}

# The actual result will include session_id from the mocked repository
GET_DEPENDENCY_GRAPH_MOCK = {
    "session_id": [SESSION_ROW_FIXTURE.id],
    **GET_DEPENDENCY_GRAPH_BASE,
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
                    session_data=SESSION_FIXTURE_DATA,
                ),
            ),
            GET_DEPENDENCY_GRAPH_BASE,
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
    mock_session_repository_methods,
    processors: SessionProcessors,
    test_scenario: TestScenario[GetDependencyGraphAction, GetDependencyGraphActionResult],
):
    await test_scenario.test(processors.get_dependency_graph.wait_for_complete)
