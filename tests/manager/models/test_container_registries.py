import pytest
from aioresponses import aioresponses
from graphene import Schema
from graphene.test import Client

from ai.backend.common.utils import b64encode
from ai.backend.manager.api.context import RootContext
from ai.backend.manager.defs import PASSWORD_PLACEHOLDER
from ai.backend.manager.models.gql import GraphQueryContext, Mutations, Queries
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.server import (
    database_ctx,
)

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
        network_plugin_ctx=None,  # type: ignore
        redis_stat=None,  # type: ignore
        redis_image=None,  # type: ignore
        redis_live=None,  # type: ignore
        manager_status=None,  # type: ignore
        known_slot_types=None,  # type: ignore
        background_task_manager=None,  # type: ignore
        storage_manager=None,  # type: ignore
        registry=None,  # type: ignore
        idle_checker_host=None,  # type: ignore
        services_ctx=None,  # type: ignore
    )


@pytest.mark.dependency()
@pytest.mark.asyncio
async def test_create_container_registry(client: Client, database_engine: ExtendedAsyncSAEngine):
    context = get_graphquery_context(database_engine)

    query = """
            mutation CreateContainerRegistry($hostname: String!, $props: CreateContainerRegistryInput!) {
                create_container_registry(hostname: $hostname, props: $props) {
                    container_registry {
                        $CONTAINER_REGISTRY_FIELDS
                    }
                }
            }
        """.replace("$CONTAINER_REGISTRY_FIELDS", CONTAINER_REGISTRY_FIELDS)

    variables = {
        "hostname": "cr.example.com",
        "props": {
            "url": "http://cr.example.com",
            "type": "docker",
            "project": ["default"],
            "username": "username",
            "password": "password",
            "ssl_verify": False,
            "is_global": False,
        },
    }

    response = await client.execute_async(query, variables=variables, context_value=context)

    container_registry = response["data"]["create_container_registry"]["container_registry"]

    assert container_registry["config"] == {
        "url": "http://cr.example.com",
        "type": "docker",
        "project": ["default"],
        "username": "username",
        "password": PASSWORD_PLACEHOLDER,
        "ssl_verify": False,
        "is_global": False,
    }


@pytest.mark.dependency(depends=["test_create_container_registry"])
@pytest.mark.asyncio
async def test_modify_container_registry(client: Client, database_engine: ExtendedAsyncSAEngine):
    context = get_graphquery_context(database_engine)

    query = """
            mutation ModifyContainerRegistry($hostname: String!, $props: ModifyContainerRegistryInput!) {
                modify_container_registry(hostname: $hostname, props: $props) {
                    container_registry {
                        $CONTAINER_REGISTRY_FIELDS
                    }
                }
            }
        """.replace("$CONTAINER_REGISTRY_FIELDS", CONTAINER_REGISTRY_FIELDS)

    variables = {
        "hostname": "cr.example.com",
        "props": {
            "username": "username2",
        },
    }

    response = await client.execute_async(query, variables=variables, context_value=context)

    container_registry = response["data"]["modify_container_registry"]["container_registry"]
    assert container_registry["config"]["url"] == "http://cr.example.com"
    assert container_registry["config"]["type"] == "docker"
    assert container_registry["config"]["project"] == ["default"]
    assert container_registry["config"]["username"] == "username2"
    assert container_registry["config"]["ssl_verify"] is False
    assert container_registry["config"]["is_global"] is False

    variables = {
        "hostname": "cr.example.com",
        "props": {
            "url": "http://cr2.example.com",
            "type": "harbor2",
            "project": ["example"],
        },
    }

    response = await client.execute_async(query, variables=variables, context_value=context)
    container_registry = response["data"]["modify_container_registry"]["container_registry"]

    assert container_registry["config"]["url"] == "http://cr2.example.com"
    assert container_registry["config"]["type"] == "harbor2"
    assert container_registry["config"]["project"] == ["example"]
    assert container_registry["config"]["username"] == "username2"
    assert container_registry["config"]["ssl_verify"] is False
    assert container_registry["config"]["is_global"] is False


@pytest.mark.dependency(depends=["test_modify_container_registry"])
@pytest.mark.asyncio
async def test_modify_container_registry_allows_empty_string(
    client: Client, database_engine: ExtendedAsyncSAEngine
):
    context = get_graphquery_context(database_engine)

    query = """
            mutation ModifyContainerRegistry($hostname: String!, $props: ModifyContainerRegistryInput!) {
                modify_container_registry(hostname: $hostname, props: $props) {
                    container_registry {
                        $CONTAINER_REGISTRY_FIELDS
                    }
                }
            }
        """.replace("$CONTAINER_REGISTRY_FIELDS", CONTAINER_REGISTRY_FIELDS)

    # Given an empty string to password
    variables = {
        "hostname": "cr.example.com",
        "props": {
            "password": "",
        },
    }

    # Then password is set to empty string
    response = await client.execute_async(query, variables=variables, context_value=context)
    container_registry = response["data"]["modify_container_registry"]["container_registry"]
    assert container_registry["config"]["url"] == "http://cr2.example.com"
    assert container_registry["config"]["type"] == "harbor2"
    assert container_registry["config"]["project"] == ["example"]
    assert container_registry["config"]["username"] == "username2"
    assert container_registry["config"]["password"] == PASSWORD_PLACEHOLDER
    assert container_registry["config"]["ssl_verify"] is False
    assert container_registry["config"]["is_global"] is False


@pytest.mark.dependency(depends=["test_modify_container_registry_allows_empty_string"])
@pytest.mark.asyncio
async def test_modify_container_registry_allows_null_for_unset(
    client: Client, database_engine: ExtendedAsyncSAEngine
):
    context = get_graphquery_context(database_engine)

    query = """
            mutation ModifyContainerRegistry($hostname: String!, $props: ModifyContainerRegistryInput!) {
                modify_container_registry(hostname: $hostname, props: $props) {
                    container_registry {
                        $CONTAINER_REGISTRY_FIELDS
                    }
                }
            }
        """.replace("$CONTAINER_REGISTRY_FIELDS", CONTAINER_REGISTRY_FIELDS)

    # Given a null to password
    variables = {
        "hostname": "cr.example.com",
        "props": {
            "password": None,
        },
    }

    # Then password is unset
    response = await client.execute_async(query, variables=variables, context_value=context)
    container_registry = response["data"]["modify_container_registry"]["container_registry"]
    assert container_registry["config"]["url"] == "http://cr2.example.com"
    assert container_registry["config"]["type"] == "harbor2"
    assert container_registry["config"]["project"] == ["example"]
    assert container_registry["config"]["username"] == "username2"
    assert container_registry["config"]["password"] is None
    assert container_registry["config"]["ssl_verify"] is False
    assert container_registry["config"]["is_global"] is False


@pytest.mark.dependency(depends=["test_modify_container_registry_allows_null_for_unset"])
@pytest.mark.asyncio
async def test_delete_container_registry(client: Client, database_engine: ExtendedAsyncSAEngine):
    context = get_graphquery_context(database_engine)

    query = """
            mutation DeleteContainerRegistry($hostname: String!) {
                delete_container_registry(hostname: $hostname) {
                    container_registry {
                        $CONTAINER_REGISTRY_FIELDS
                    }
                }
            }
        """.replace("$CONTAINER_REGISTRY_FIELDS", CONTAINER_REGISTRY_FIELDS)

    variables = {
        "hostname": "cr.example.com",
    }

    response = await client.execute_async(query, variables=variables, context_value=context)

    container_registry = response["data"]["delete_container_registry"]["container_registry"]
    assert container_registry["hostname"] == "cr.example.com"

    query = """
        query ContainerRegistries() {
            container_registries () {
                $CONTAINER_REGISTRY_FIELDS
            }
        }
        """.replace("$CONTAINER_REGISTRY_FIELDS", CONTAINER_REGISTRY_FIELDS)

    response = await client.execute_async(query, variables=variables, context_value=context)
    assert response["data"] is None


FIXTURES_FOR_HARBOR_CRUD_TEST = [
    {
        "container_registries": [
            {
                "id": "00000000-0000-0000-0000-000000000000",
                "type": "harbor2",
                "url": "http://mock_registry",
                "registry_name": "mock_registry",
                "project": "mock_project",
                "username": "mock_user",
                "password": "mock_password",
                "ssl_verify": False,
                "is_global": True,
            }
        ],
        "groups": [
            {
                "id": "00000000-0000-0000-0000-000000000000",
                "name": "mock_group",
                "description": "",
                "is_active": True,
                "domain_name": "default",
                "resource_policy": "default",
                "total_resource_slots": {},
                "allowed_vfolder_hosts": {},
                "container_registry": {
                    "registry": "mock_registry",
                    "project": "mock_project",
                },
                "type": "general",
            }
        ],
    },
]


@pytest.mark.asyncio
@pytest.mark.parametrize("extra_fixtures", FIXTURES_FOR_HARBOR_CRUD_TEST)
async def test_harbor_read_project_quota(
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
    HARBOR_QUOTA_VALUE = 1024

    with aioresponses() as mocked:
        get_project_id_url = "http://mock_registry/api/v2.0/projects/mock_project"
        mocked.get(get_project_id_url, status=200, payload={"project_id": HARBOR_PROJECT_ID})

        get_quota_url = f"http://mock_registry/api/v2.0/quotas?reference=project&reference_id={HARBOR_PROJECT_ID}"
        mocked.get(
            get_quota_url,
            status=200,
            payload=[{"id": HARBOR_QUOTA_ID, "hard": {"storage": HARBOR_QUOTA_VALUE}}],
        )

        groupnode_query = """
            query ($id: String!) {
                group_node(id: $id) {
                    registry_quota
                }
            }
        """

        group_id = "00000000-0000-0000-0000-000000000000"
        variables = {
            "id": b64encode(f"group_node:{group_id}"),
        }

        response = await client.execute_async(
            groupnode_query, variables=variables, context_value=context
        )
        assert response["data"]["group_node"]["registry_quota"] == HARBOR_QUOTA_VALUE


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
