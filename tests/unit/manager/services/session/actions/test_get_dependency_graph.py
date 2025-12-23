from typing import cast

import pytest

from ai.backend.common.types import AccessKey
from ai.backend.manager.services.session.actions.get_dependency_graph import (
    GetDependencyGraphAction,
    GetDependencyGraphActionResult,
)
from ai.backend.manager.services.session.processors import SessionProcessors

from ...utils import ScenarioBase
from ..fixtures import (
    AGENT_FIXTURE_DICT,
    GROUP_FIXTURE_DATA,
    GROUP_USER_ASSOCIATION_DATA,
    KERNEL_FIXTURE_DICT,
    KERNEL_FIXTURE_DICT2,
    SESSION_FIXTURE_DATA,
    SESSION_FIXTURE_DATA2,
    SESSION_FIXTURE_DICT,
    SESSION_FIXTURE_DICT2,
    SESSION_ROW_FIXTURE,
    USER_FIXTURE_DATA,
)

GET_DEPENDENCY_GRAPH_BASE = {
    "nodes": [{"id": "node1", "type": "function"}],
    "edges": [{"from": "node1", "to": "node2"}],
    "session_id": [SESSION_ROW_FIXTURE.id],
}

# The actual result will include session_id from the mocked repository
GET_DEPENDENCY_GRAPH_MOCK = {
    "session_id": [SESSION_ROW_FIXTURE.id],
    **GET_DEPENDENCY_GRAPH_BASE,
}

# Mock result with child sessions for dependency graph testing
GET_DEPENDENCY_GRAPH_WITH_CHILD_MOCK = {
    "nodes": [{"id": "node1", "type": "function"}, {"id": "node2", "type": "function"}],
    "edges": [{"from": "node1", "to": "node2"}],
    "session_id": [SESSION_ROW_FIXTURE.id, SESSION_FIXTURE_DATA2.id],
}


@pytest.mark.skip(reason="WIP, Need to be fixed")
@pytest.mark.parametrize(
    "test_scenario",
    [
        ScenarioBase.success(
            "Get dependency graph",
            GetDependencyGraphAction(
                root_session_name=cast(str, SESSION_FIXTURE_DATA.name),
                owner_access_key=cast(AccessKey, SESSION_FIXTURE_DATA.access_key),
            ),
            GetDependencyGraphActionResult(
                result=GET_DEPENDENCY_GRAPH_WITH_CHILD_MOCK,
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
            "sessions": [SESSION_FIXTURE_DICT, SESSION_FIXTURE_DICT2],
            "kernels": [KERNEL_FIXTURE_DICT, KERNEL_FIXTURE_DICT2],
            "users": [USER_FIXTURE_DATA],
            "groups": [GROUP_FIXTURE_DATA],
            "association_groups_users": [GROUP_USER_ASSOCIATION_DATA],
            "session_dependencies": [
                {
                    "session_id": SESSION_FIXTURE_DATA.id,
                    "depends_on": SESSION_FIXTURE_DATA2.id,
                }
            ],
        }
    ],
)
async def test_get_dependency_graph(
    processors: SessionProcessors,
    test_scenario: ScenarioBase[GetDependencyGraphAction, GetDependencyGraphActionResult],
    session_repository,
):
    await test_scenario.test(processors.get_dependency_graph.wait_for_complete)
