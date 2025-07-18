from typing import cast

import pytest

from ai.backend.common.types import AccessKey
from ai.backend.manager.services.session.actions.get_dependency_graph import (
    GetDependencyGraphAction,
    GetDependencyGraphActionResult,
)
from ai.backend.manager.services.session.processors import SessionProcessors

from ...test_utils import TestScenario
from ..fixtures import (
    GROUP_FIXTURE_DATA,
    GROUP_USER_ASSOCIATION_DATA,
    KERNEL_FIXTURE_DICT,
    SESSION_FIXTURE_DATA,
    SESSION_FIXTURE_DICT,
    SESSION_ROW_FIXTURE,
    USER_FIXTURE_DATA,
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
            "users": [USER_FIXTURE_DATA],
            "groups": [GROUP_FIXTURE_DATA],
            "association_groups_users": [GROUP_USER_ASSOCIATION_DATA],
        }
    ],
)
async def test_get_dependency_graph(
    mock_session_repository_methods,
    processors: SessionProcessors,
    test_scenario: TestScenario[GetDependencyGraphAction, GetDependencyGraphActionResult],
    session_repository,
):
    await test_scenario.test(processors.get_dependency_graph.wait_for_complete)
