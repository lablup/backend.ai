import pytest
from aioresponses import aioresponses
from graphene import Schema
from graphene.test import Client

from ai.backend.manager.api.context import RootContext
from ai.backend.manager.models.gql import GraphQueryContext, Mutations, Queries
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.server import (
    database_ctx,
)
from ai.backend.testutils.extra_fixtures import FIXTURES_FOR_HARBOR_CRUD_TEST


@pytest.fixture(scope="module")
def client() -> Client:
    return Client(Schema(query=Queries, mutation=Mutations, auto_camelcase=False))


def get_graphquery_context(database_engine: ExtendedAsyncSAEngine) -> GraphQueryContext:
    return GraphQueryContext(
        schema=None,  # type: ignore
        dataloader_manager=None,  # type: ignore
        local_config=None,  # type: ignore
        shared_config=None,  # type: ignore
        etcd=None,  # type: ignore
        user={"domain": "default", "role": "superadmin"},
        access_key="AKIAIOSFODNN7EXAMPLE",
        db=database_engine,  # type: ignore
        redis_stat=None,  # type: ignore
        redis_image=None,  # type: ignore
        redis_live=None,  # type: ignore
        manager_status=None,  # type: ignore
        known_slot_types=None,  # type: ignore
        background_task_manager=None,  # type: ignore
        storage_manager=None,  # type: ignore
        registry=None,  # type: ignore
        idle_checker_host=None,  # type: ignore
    )


FIXTURES_WITH_NOASSOC = [
    {
        "groups": [
            {
                "id": "00000000-0000-0000-0000-000000000001",
                "name": "mock_group",
                "description": "",
                "is_active": True,
                "domain_name": "default",
                "resource_policy": "default",
                "total_resource_slots": {},
                "allowed_vfolder_hosts": {},
                "type": "general",
            }
        ],
        "container_registries": [
            {
                "id": "00000000-0000-0000-0000-000000000002",
                "url": "https://mock.registry.com",
                "type": "docker",
                "project": "mock_project",
                "registry_name": "mock_registry",
            }
        ],
    }
]

FIXTURES_WITH_ASSOC = [
    {
        **fixture,
        "association_container_registries_groups": [
            {
                "id": "00000000-0000-0000-0000-000000000000",
                "group_id": "00000000-0000-0000-0000-000000000001",
                "registry_id": "00000000-0000-0000-0000-000000000002",
            }
        ],
    }
    for fixture in FIXTURES_WITH_NOASSOC
]


@pytest.mark.dependency()
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "extra_fixtures",
    FIXTURES_WITH_NOASSOC + FIXTURES_WITH_ASSOC,
    ids=["(No association)", "(With association)"],
)
@pytest.mark.parametrize(
    "test_case",
    [
        {
            "group_id": "00000000-0000-0000-0000-000000000001",
            "registry_id": "00000000-0000-0000-0000-000000000002",
        },
    ],
    ids=["Associate One group with one container registry"],
)
async def test_associate_container_registry_with_group(
    client: Client, database_fixture, extra_fixtures, test_case, create_app_and_client
):
    test_app, _ = await create_app_and_client(
        [
            database_ctx,
        ],
        [],
    )

    root_ctx = test_app["_root.context"]
    context = get_graphquery_context(root_ctx.db)

    query = """
        mutation ($group_id: String!, $registry_id: String!) {
            associate_container_registry_with_group(group_id: $group_id, registry_id: $registry_id) {
                ok
                msg
            }
        }
        """

    variables = {
        "group_id": test_case["group_id"],
        "registry_id": test_case["registry_id"],
    }

    response = await client.execute_async(query, variables=variables, context_value=context)
    already_associated = "association_container_registries_groups" in extra_fixtures

    if already_associated:
        assert not response["data"]["associate_container_registry_with_group"]["ok"]
    else:
        assert response["data"]["associate_container_registry_with_group"]["ok"]
        assert response["data"]["associate_container_registry_with_group"]["msg"] == "success"


@pytest.mark.dependency()
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "extra_fixtures",
    FIXTURES_WITH_ASSOC + FIXTURES_WITH_NOASSOC,
    ids=["(With association)", "(No association)"],
)
@pytest.mark.parametrize(
    "test_case",
    [
        {
            "group_id": "00000000-0000-0000-0000-000000000001",
            "registry_id": "00000000-0000-0000-0000-000000000002",
        },
    ],
    ids=["Disassociate One group with one container registry"],
)
async def test_disassociate_container_registry_with_group(
    client: Client, database_fixture, extra_fixtures, test_case, create_app_and_client
):
    test_app, _ = await create_app_and_client(
        [
            database_ctx,
        ],
        [],
    )

    root_ctx = test_app["_root.context"]
    context = get_graphquery_context(root_ctx.db)

    query = """
        mutation ($group_id: String!, $registry_id: String!) {
            disassociate_container_registry_with_group(group_id: $group_id, registry_id: $registry_id) {
                ok
                msg
            }
        }
        """

    variables = {
        "group_id": test_case["group_id"],
        "registry_id": test_case["registry_id"],
    }

    response = await client.execute_async(query, variables=variables, context_value=context)
    association_exist = "association_container_registries_groups" in extra_fixtures

    if association_exist:
        assert response["data"]["disassociate_container_registry_with_group"]["ok"]
        assert response["data"]["disassociate_container_registry_with_group"]["msg"] == "success"
    else:
        assert not response["data"]["disassociate_container_registry_with_group"]["ok"]


CONTAINER_REGISTRY_FIELDS = """
    hostname
    config {
        url
        type
        project
        username
        password
        ssl_verify
        is_global
    }
"""


@pytest.fixture(scope="module")
def client() -> Client:
    return Client(Schema(query=Queries, mutation=Mutations, auto_camelcase=False))


def get_graphquery_context(database_engine: ExtendedAsyncSAEngine) -> GraphQueryContext:
    return GraphQueryContext(
        schema=None,  # type: ignore
        dataloader_manager=None,  # type: ignore
        local_config=None,  # type: ignore
        shared_config=None,  # type: ignore
        etcd=None,  # type: ignore
        user={"domain": "default", "role": "superadmin"},
        access_key="AKIAIOSFODNN7EXAMPLE",
        db=database_engine,  # type: ignore
        redis_stat=None,  # type: ignore
        redis_image=None,  # type: ignore
        redis_live=None,  # type: ignore
        manager_status=None,  # type: ignore
        known_slot_types=None,  # type: ignore
        background_task_manager=None,  # type: ignore
        storage_manager=None,  # type: ignore
        registry=None,  # type: ignore
        idle_checker_host=None,  # type: ignore
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("extra_fixtures", FIXTURES_FOR_HARBOR_CRUD_TEST)
async def test_harbor_create_project_quota(
    client: Client,
    database_fixture,
    create_app_and_client,
):
    test_app, _ = await create_app_and_client(
        [
            database_ctx,
        ],
        [],
    )

    root_ctx: RootContext = test_app["_root.context"]
    context = get_graphquery_context(root_ctx.db)

    # Arbitrary values for mocking Harbor API responses
    HARBOR_PROJECT_ID = "123"
    HARBOR_QUOTA_ID = 456

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

    # Normal case: create a new quota
    with aioresponses() as mocked:
        get_project_id_url = "http://mock_registry/api/v2.0/projects/mock_project"
        mocked.get(get_project_id_url, status=200, payload={"project_id": HARBOR_PROJECT_ID})

        get_quota_url = f"http://mock_registry/api/v2.0/quotas?reference=project&reference_id={HARBOR_PROJECT_ID}"
        mocked.get(
            get_quota_url,
            status=200,
            payload=[{"id": HARBOR_QUOTA_ID, "hard": {"storage": -1}}],
        )

        put_quota_url = f"http://mock_registry/api/v2.0/quotas/{HARBOR_QUOTA_ID}"
        mocked.put(
            put_quota_url,
            status=200,
        )

        response = await client.execute_async(
            create_query, variables=variables, context_value=context
        )
        assert response["data"]["create_container_registry_quota"]["ok"]
        assert response["data"]["create_container_registry_quota"]["msg"] == "success"

    # If the quota already exists, the mutation should fail
    with aioresponses() as mocked:
        get_project_id_url = "http://mock_registry/api/v2.0/projects/mock_project"
        mocked.get(get_project_id_url, status=200, payload={"project_id": HARBOR_PROJECT_ID})

        get_quota_url = f"http://mock_registry/api/v2.0/quotas?reference=project&reference_id={HARBOR_PROJECT_ID}"
        mocked.get(
            get_quota_url,
            status=200,
            payload=[{"id": HARBOR_QUOTA_ID, "hard": {"storage": 100}}],
        )

        response = await client.execute_async(
            create_query, variables=variables, context_value=context
        )
        assert not response["data"]["create_container_registry_quota"]["ok"]


@pytest.mark.asyncio
@pytest.mark.parametrize("extra_fixtures", FIXTURES_FOR_HARBOR_CRUD_TEST)
async def test_harbor_update_project_quota(
    client: Client,
    database_fixture,
    create_app_and_client,
):
    test_app, _ = await create_app_and_client(
        [
            database_ctx,
        ],
        [],
    )

    root_ctx: RootContext = test_app["_root.context"]
    context = get_graphquery_context(root_ctx.db)

    # Arbitrary values for mocking Harbor API responses
    HARBOR_PROJECT_ID = "123"
    HARBOR_QUOTA_ID = 456

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

    # Normal case: update quota
    with aioresponses() as mocked:
        get_project_id_url = "http://mock_registry/api/v2.0/projects/mock_project"
        mocked.get(get_project_id_url, status=200, payload={"project_id": HARBOR_PROJECT_ID})

        get_quota_url = f"http://mock_registry/api/v2.0/quotas?reference=project&reference_id={HARBOR_PROJECT_ID}"
        mocked.get(
            get_quota_url,
            status=200,
            payload=[{"id": HARBOR_QUOTA_ID, "hard": {"storage": 100}}],
        )

        put_quota_url = f"http://mock_registry/api/v2.0/quotas/{HARBOR_QUOTA_ID}"
        mocked.put(
            put_quota_url,
            status=200,
        )

        response = await client.execute_async(
            update_query, variables=variables, context_value=context
        )
        assert response["data"]["update_container_registry_quota"]["ok"]
        assert response["data"]["update_container_registry_quota"]["msg"] == "success"

    # If the quota doesn't exist, the mutation should fail
    with aioresponses() as mocked:
        get_project_id_url = "http://mock_registry/api/v2.0/projects/mock_project"
        mocked.get(get_project_id_url, status=200, payload={"project_id": HARBOR_PROJECT_ID})

        get_quota_url = f"http://mock_registry/api/v2.0/quotas?reference=project&reference_id={HARBOR_PROJECT_ID}"
        mocked.get(
            get_quota_url,
            status=200,
            payload=[{"id": HARBOR_QUOTA_ID, "hard": {"storage": -1}}],
        )

        response = await client.execute_async(
            update_query, variables=variables, context_value=context
        )
        assert not response["data"]["update_container_registry_quota"]["ok"]


@pytest.mark.asyncio
@pytest.mark.parametrize("extra_fixtures", FIXTURES_FOR_HARBOR_CRUD_TEST)
async def test_harbor_delete_project_quota(
    client: Client,
    database_fixture,
    create_app_and_client,
):
    test_app, _ = await create_app_and_client(
        [
            database_ctx,
        ],
        [],
    )

    root_ctx: RootContext = test_app["_root.context"]
    context = get_graphquery_context(root_ctx.db)

    # Arbitrary values for mocking Harbor API responses
    HARBOR_PROJECT_ID = "123"
    HARBOR_QUOTA_ID = 456

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

    # Normal case: delete quota
    with aioresponses() as mocked:
        get_project_id_url = "http://mock_registry/api/v2.0/projects/mock_project"
        mocked.get(get_project_id_url, status=200, payload={"project_id": HARBOR_PROJECT_ID})

        get_quota_url = f"http://mock_registry/api/v2.0/quotas?reference=project&reference_id={HARBOR_PROJECT_ID}"
        mocked.get(
            get_quota_url,
            status=200,
            payload=[{"id": HARBOR_QUOTA_ID, "hard": {"storage": 100}}],
        )

        put_quota_url = f"http://mock_registry/api/v2.0/quotas/{HARBOR_QUOTA_ID}"
        mocked.put(
            put_quota_url,
            status=200,
        )

        response = await client.execute_async(
            delete_query, variables=variables, context_value=context
        )
        assert response["data"]["delete_container_registry_quota"]["ok"]
        assert response["data"]["delete_container_registry_quota"]["msg"] == "success"

    # If the quota doesn't exist, the mutation should fail
    with aioresponses() as mocked:
        get_project_id_url = "http://mock_registry/api/v2.0/projects/mock_project"
        mocked.get(get_project_id_url, status=200, payload={"project_id": HARBOR_PROJECT_ID})

        get_quota_url = f"http://mock_registry/api/v2.0/quotas?reference=project&reference_id={HARBOR_PROJECT_ID}"
        mocked.get(
            get_quota_url,
            status=200,
            payload=[{"id": HARBOR_QUOTA_ID, "hard": {"storage": -1}}],
        )

        response = await client.execute_async(
            delete_query, variables=variables, context_value=context
        )
        assert not response["data"]["delete_container_registry_quota"]["ok"]
