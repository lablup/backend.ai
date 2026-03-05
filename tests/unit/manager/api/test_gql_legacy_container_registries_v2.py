from typing import Any

import pytest
from graphene import Schema
from graphene.test import Client

from ai.backend.common.metrics.metric import GraphQLMetricObserver
from ai.backend.manager.api.gql_legacy.schema import GraphQueryContext, Mutation, Query
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.extra_fixtures import FIXTURES_FOR_HARBOR_CRUD_TEST

# TODO: These tests require services_ctx (harbor quota service) which is not
# yet available through the current test fixture pattern.
# They need to be refactored to inject the quota service directly.


@pytest.fixture(scope="module")
def client() -> Client:
    return Client(Schema(query=Query, mutation=Mutation, auto_camelcase=False))


def get_graphquery_context(
    database_engine: ExtendedAsyncSAEngine, services_ctx: Any
) -> GraphQueryContext:
    return GraphQueryContext(
        schema=None,
        dataloader_manager=None,  # type: ignore
        config_provider=None,  # type: ignore
        etcd=None,  # type: ignore
        user={"domain": "default", "role": "superadmin"},
        access_key="AKIAIOSFODNN7EXAMPLE",
        db=database_engine,
        valkey_stat=None,  # type: ignore
        valkey_image=None,  # type: ignore
        valkey_live=None,  # type: ignore
        valkey_schedule=None,  # type: ignore
        manager_status=None,  # type: ignore
        known_slot_types=None,  # type: ignore
        background_task_manager=None,  # type: ignore
        storage_manager=None,  # type: ignore
        registry=None,  # type: ignore
        idle_checker_host=None,  # type: ignore
        network_plugin_ctx=None,  # type: ignore
        services_ctx=services_ctx,
        metric_observer=GraphQLMetricObserver.instance(),
        processors=None,  # type: ignore
        scheduler_repository=None,  # type: ignore
        user_repository=None,  # type: ignore
        agent_repository=None,  # type: ignore
    )


@pytest.mark.skip(
    reason="Needs services_ctx (harbor quota service) -- not available via test fixtures yet"
)
@pytest.mark.parametrize("extra_fixtures", FIXTURES_FOR_HARBOR_CRUD_TEST, indirect=True)
@pytest.mark.parametrize(
    "test_case",
    [
        {
            "mock_harbor_responses": {
                "get_project_id": {"project_id": "1"},
                "get_quotas": [
                    {
                        "id": 1,
                        "hard": {"storage": -1},
                    }
                ],
            },
            "expected": True,
        },
        {
            "mock_harbor_responses": {
                "get_project_id": {"project_id": "1"},
                "get_quotas": [
                    {
                        "id": 1,
                        "hard": {"storage": 100},
                    }
                ],
            },
            "expected": False,
        },
    ],
    ids=["Normal case", "Project Quota already exist"],
)
async def test_harbor_create_project_quota(
    client: Client,
    test_case: dict[str, Any],
    database_fixture: None,
    database_engine: ExtendedAsyncSAEngine,
) -> None:
    # Requires services_ctx to provide harbor quota service
    pass


@pytest.mark.skip(
    reason="Needs services_ctx (harbor quota service) -- not available via test fixtures yet"
)
@pytest.mark.parametrize("extra_fixtures", FIXTURES_FOR_HARBOR_CRUD_TEST, indirect=True)
@pytest.mark.parametrize(
    "test_case",
    [
        {
            "mock_harbor_responses": {
                "get_project_id": {"project_id": "1"},
                "get_quotas": [
                    {
                        "id": 1,
                        "hard": {"storage": 100},
                    }
                ],
            },
            "expected": True,
        },
        {
            "mock_harbor_responses": {
                "get_project_id": {"project_id": "1"},
                "get_quotas": [
                    {
                        "id": 1,
                        "hard": {"storage": -1},
                    }
                ],
            },
            "expected": False,
        },
    ],
    ids=["Normal case", "Project Quota not found"],
)
async def test_harbor_update_project_quota(
    client: Client,
    test_case: dict[str, Any],
    database_fixture: None,
    database_engine: ExtendedAsyncSAEngine,
) -> None:
    # Requires services_ctx to provide harbor quota service
    pass


@pytest.mark.skip(
    reason="Needs services_ctx (harbor quota service) -- not available via test fixtures yet"
)
@pytest.mark.parametrize("extra_fixtures", FIXTURES_FOR_HARBOR_CRUD_TEST, indirect=True)
@pytest.mark.parametrize(
    "test_case",
    [
        {
            "mock_harbor_responses": {
                "get_project_id": {"project_id": "1"},
                "get_quotas": [
                    {
                        "id": 1,
                        "hard": {"storage": 100},
                    }
                ],
            },
            "expected": True,
        },
        {
            "mock_harbor_responses": {
                "get_project_id": {"project_id": "1"},
                "get_quotas": [
                    {
                        "id": 1,
                        "hard": {"storage": -1},
                    }
                ],
            },
            "expected": False,
        },
    ],
    ids=["Normal case", "Project Quota not found"],
)
async def test_harbor_delete_project_quota(
    client: Client,
    test_case: dict[str, Any],
    database_fixture: None,
    database_engine: ExtendedAsyncSAEngine,
) -> None:
    # Requires services_ctx to provide harbor quota service
    pass
