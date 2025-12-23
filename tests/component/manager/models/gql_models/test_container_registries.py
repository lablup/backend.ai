from http import HTTPStatus

import pytest
from aioresponses import aioresponses
from graphene import Schema
from graphene.test import Client

from ai.backend.common.metrics.metric import GraphQLMetricObserver
from ai.backend.manager.api.context import RootContext
from ai.backend.manager.models.gql import GraphQueryContext, Mutation, Query
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.server import (
    database_ctx,
    services_ctx,
)
from ai.backend.testutils.extra_fixtures import FIXTURES_FOR_HARBOR_CRUD_TEST


@pytest.fixture(scope="module")
def client() -> Client:
    return Client(Schema(query=Query, mutation=Mutation, auto_camelcase=False))


def get_graphquery_context(
    database_engine: ExtendedAsyncSAEngine, services_ctx
) -> GraphQueryContext:
    return GraphQueryContext(
        schema=None,  # type: ignore
        dataloader_manager=None,  # type: ignore
        config_provider=None,  # type: ignore
        etcd=None,  # type: ignore
        user={"domain": "default", "role": "superadmin"},
        access_key="AKIAIOSFODNN7EXAMPLE",
        db=database_engine,  # type: ignore
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
        services_ctx=services_ctx,  # type: ignore
        metric_observer=GraphQLMetricObserver.instance(),
        processors=None,  # type: ignore
        scheduler_repository=None,  # type: ignore
        user_repository=None,  # type: ignore
        agent_repository=None,  # type: ignore
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("extra_fixtures", FIXTURES_FOR_HARBOR_CRUD_TEST)
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
    test_case,
    mock_etcd_ctx,
    mock_config_provider_ctx,
    database_fixture,
    create_app_and_client,
):
    test_app, _ = await create_app_and_client(
        [
            mock_etcd_ctx,
            mock_config_provider_ctx,
            database_ctx,
            services_ctx,
        ],
        [],
    )

    root_ctx: RootContext = test_app["_root.context"]
    context = get_graphquery_context(root_ctx.db, root_ctx.services_ctx)

    create_query = """
        mutation ($scope_id: ScopeField!, $quota: BigInt!) {
            create_container_registry_quota(scope_id: $scope_id, quota: $quota) {
                ok
                msg
            }
        }
    """
    variables = {
        "scope_id": "project:00000000-0000-0000-0000-000000000000",
        "quota": 100,
    }

    mock_harbor_responses = test_case["mock_harbor_responses"]

    with aioresponses() as mocked:
        get_project_id_url = "http://mock_registry/api/v2.0/projects/mock_project"
        mocked.get(
            get_project_id_url,
            status=HTTPStatus.OK,
            payload=mock_harbor_responses["get_project_id"],
        )

        harbor_project_id = mock_harbor_responses["get_project_id"]["project_id"]
        get_quotas_url = f"http://mock_registry/api/v2.0/quotas?reference=project&reference_id={harbor_project_id}"
        mocked.get(
            get_quotas_url,
            status=HTTPStatus.OK,
            payload=mock_harbor_responses["get_quotas"],
        )

        harbor_quota_id = mock_harbor_responses["get_quotas"][0]["id"]
        put_quota_url = f"http://mock_registry/api/v2.0/quotas/{harbor_quota_id}"
        mocked.put(
            put_quota_url,
            status=HTTPStatus.OK,
        )

        response = await client.execute_async(
            create_query, variables=variables, context_value=context
        )

        assert response["data"]["create_container_registry_quota"]["ok"] == test_case["expected"]


@pytest.mark.asyncio
@pytest.mark.parametrize("extra_fixtures", FIXTURES_FOR_HARBOR_CRUD_TEST)
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
    test_case,
    mock_etcd_ctx,
    mock_config_provider_ctx,
    database_fixture,
    create_app_and_client,
):
    test_app, _ = await create_app_and_client(
        [
            mock_etcd_ctx,
            mock_config_provider_ctx,
            database_ctx,
            services_ctx,
        ],
        [],
    )

    root_ctx: RootContext = test_app["_root.context"]
    context = get_graphquery_context(root_ctx.db, root_ctx.services_ctx)

    update_query = """
        mutation ($scope_id: ScopeField!, $quota: BigInt!) {
            update_container_registry_quota(scope_id: $scope_id, quota: $quota) {
                ok
                msg
            }
        }
    """
    variables = {
        "scope_id": "project:00000000-0000-0000-0000-000000000000",
        "quota": 200,
    }

    mock_harbor_responses = test_case["mock_harbor_responses"]

    with aioresponses() as mocked:
        get_project_id_url = "http://mock_registry/api/v2.0/projects/mock_project"
        mocked.get(
            get_project_id_url,
            status=HTTPStatus.OK,
            payload=mock_harbor_responses["get_project_id"],
        )

        harbor_project_id = mock_harbor_responses["get_project_id"]["project_id"]

        get_quotas_url = f"http://mock_registry/api/v2.0/quotas?reference=project&reference_id={harbor_project_id}"
        mocked.get(
            get_quotas_url,
            status=HTTPStatus.OK,
            payload=mock_harbor_responses["get_quotas"],
        )

        harbor_quota_id = mock_harbor_responses["get_quotas"][0]["id"]
        put_quota_url = f"http://mock_registry/api/v2.0/quotas/{harbor_quota_id}"
        mocked.put(
            put_quota_url,
            status=HTTPStatus.OK,
        )

        response = await client.execute_async(
            update_query, variables=variables, context_value=context
        )
        assert response["data"]["update_container_registry_quota"]["ok"] == test_case["expected"]


@pytest.mark.asyncio
@pytest.mark.parametrize("extra_fixtures", FIXTURES_FOR_HARBOR_CRUD_TEST)
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
    test_case,
    mock_etcd_ctx,
    mock_config_provider_ctx,
    database_fixture,
    create_app_and_client,
):
    test_app, _ = await create_app_and_client(
        [
            mock_etcd_ctx,
            mock_config_provider_ctx,
            database_ctx,
            services_ctx,
        ],
        [],
    )

    root_ctx: RootContext = test_app["_root.context"]
    context = get_graphquery_context(root_ctx.db, root_ctx.services_ctx)

    delete_query = """
        mutation ($scope_id: ScopeField!) {
            delete_container_registry_quota(scope_id: $scope_id) {
                ok
                msg
            }
        }
    """
    variables = {
        "scope_id": "project:00000000-0000-0000-0000-000000000000",
    }

    mock_harbor_responses = test_case["mock_harbor_responses"]

    with aioresponses() as mocked:
        get_project_id_url = "http://mock_registry/api/v2.0/projects/mock_project"
        mocked.get(
            get_project_id_url,
            status=HTTPStatus.OK,
            payload=mock_harbor_responses["get_project_id"],
        )

        harbor_project_id = mock_harbor_responses["get_project_id"]["project_id"]

        get_quotas_url = f"http://mock_registry/api/v2.0/quotas?reference=project&reference_id={harbor_project_id}"
        mocked.get(
            get_quotas_url,
            status=HTTPStatus.OK,
            payload=mock_harbor_responses["get_quotas"],
        )

        harbor_quota_id = mock_harbor_responses["get_quotas"][0]["id"]
        put_quota_url = f"http://mock_registry/api/v2.0/quotas/{harbor_quota_id}"
        mocked.put(
            put_quota_url,
            status=HTTPStatus.OK,
        )

        response = await client.execute_async(
            delete_query, variables=variables, context_value=context
        )
        assert response["data"]["delete_container_registry_quota"]["ok"] == test_case["expected"]
