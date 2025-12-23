import pytest
from graphene import Schema
from graphene.test import Client

from ai.backend.common.metrics.metric import GraphQLMetricObserver
from ai.backend.manager.defs import PASSWORD_PLACEHOLDER
from ai.backend.manager.models.gql import GraphQueryContext, Mutation, Query
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

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
    return Client(Schema(query=Query, mutation=Mutation, auto_camelcase=False))


def get_graphquery_context(database_engine: ExtendedAsyncSAEngine) -> GraphQueryContext:
    return GraphQueryContext(
        schema=None,  # type: ignore
        dataloader_manager=None,  # type: ignore
        config_provider=None,  # type: ignore
        etcd=None,  # type: ignore
        user={"domain": "default", "role": "superadmin"},
        access_key="AKIAIOSFODNN7EXAMPLE",
        db=database_engine,  # type: ignore
        network_plugin_ctx=None,  # type: ignore
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
        services_ctx=None,  # type: ignore
        metric_observer=GraphQLMetricObserver.instance(),
        processors=None,  # type: ignore
        scheduler_repository=None,  # type: ignore
        user_repository=None,  # type: ignore
        agent_repository=None,  # type: ignore
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
