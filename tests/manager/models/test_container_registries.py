import pytest
from graphene import Schema
from graphene.test import Client

from ai.backend.manager.defs import PASSWORD_PLACEHOLDER
from ai.backend.manager.models.gql import GraphQueryContext, Mutations, Queries
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

CONTAINER_REGISTRY_FIELDS = """
    id
    config {
        registry_name
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


@pytest.mark.dependency()
@pytest.mark.asyncio
async def test_create_container_registry(client: Client, database_engine: ExtendedAsyncSAEngine):
    context = get_graphquery_context(database_engine)

    query = """
            mutation CreateContainerRegistry($props: CreateContainerRegistryInput!) {
                create_container_registry(props: $props) {
                    container_registry {
                        $CONTAINER_REGISTRY_FIELDS
                    }
                }
            }
        """.replace("$CONTAINER_REGISTRY_FIELDS", CONTAINER_REGISTRY_FIELDS)

    variables = {
        "props": {
            "registry_name": "cr.example.com",
            "url": "http://cr.example.com",
            "type": "docker",
            "project": "default",
            "username": "username",
            "password": "password",
            "ssl_verify": False,
            "is_global": False,
        },
    }

    response = await client.execute_async(query, variables=variables, context_value=context)

    container_registry = response["data"]["create_container_registry"]["container_registry"]

    id = container_registry.pop("id", None)
    assert id is not None

    assert container_registry["config"] == {
        "registry_name": "cr.example.com",
        "url": "http://cr.example.com",
        "type": "docker",
        "project": "default",
        "username": "username",
        "password": PASSWORD_PLACEHOLDER,
        "ssl_verify": False,
        "is_global": False,
    }

    variables["props"]["project"] = "default2"
    await client.execute_async(query, variables=variables, context_value=context)


@pytest.mark.dependency(depends=["test_get_container_registry"])
@pytest.mark.asyncio
async def test_modify_container_registry(client: Client, database_engine: ExtendedAsyncSAEngine):
    context = get_graphquery_context(database_engine)

    query = """
        query ContainerRegistries($registry_name: String!) {
            container_registries (registry_name: $registry_name) {
                $CONTAINER_REGISTRY_FIELDS
            }
        }
        """.replace("$CONTAINER_REGISTRY_FIELDS", CONTAINER_REGISTRY_FIELDS)

    variables: dict[str, dict | str] = {
        "registry_name": "cr.example.com",
    }

    response = await client.execute_async(query, variables=variables, context_value=context)

    target_container_registries = list(
        filter(
            lambda item: item["config"]["project"] == "default",
            response["data"]["container_registries"],
        )
    )
    assert len(target_container_registries) == 1
    target_container_registry = target_container_registries[0]

    query = """
            mutation ModifyContainerRegistry($id: String!, $props: ModifyContainerRegistryInput!) {
                modify_container_registry(id: $id, props: $props) {
                    container_registry {
                        $CONTAINER_REGISTRY_FIELDS
                    }
                }
            }
        """.replace("$CONTAINER_REGISTRY_FIELDS", CONTAINER_REGISTRY_FIELDS)

    variables = {
        "id": target_container_registry["id"],
        "props": {
            "registry_name": "cr.example.com",
            "username": "username2",
        },
    }

    response = await client.execute_async(query, variables=variables, context_value=context)

    container_registry = response["data"]["modify_container_registry"]["container_registry"]
    assert container_registry["config"]["registry_name"] == "cr.example.com"
    assert container_registry["config"]["url"] == "http://cr.example.com"
    assert container_registry["config"]["type"] == "docker"
    assert container_registry["config"]["project"] == "default"
    assert container_registry["config"]["username"] == "username2"
    assert container_registry["config"]["ssl_verify"] is False
    assert container_registry["config"]["is_global"] is False

    variables = {
        "id": target_container_registry["id"],
        "props": {
            "registry_name": "cr.example.com",
            "url": "http://cr2.example.com",
            "type": "harbor2",
            "project": "example",
        },
    }

    response = await client.execute_async(query, variables=variables, context_value=context)
    container_registry = response["data"]["modify_container_registry"]["container_registry"]

    assert container_registry["config"]["registry_name"] == "cr.example.com"
    assert container_registry["config"]["url"] == "http://cr2.example.com"
    assert container_registry["config"]["type"] == "harbor2"
    assert container_registry["config"]["project"] == "example"
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
        query ContainerRegistries($registry_name: String!) {
            container_registries (registry_name: $registry_name) {
                $CONTAINER_REGISTRY_FIELDS
            }
        }
        """.replace("$CONTAINER_REGISTRY_FIELDS", CONTAINER_REGISTRY_FIELDS)

    variables: dict[str, dict | str] = {
        "registry_name": "cr.example.com",
    }

    response = await client.execute_async(query, variables=variables, context_value=context)

    target_container_registries = list(
        filter(
            lambda item: item["config"]["project"] == "example",
            response["data"]["container_registries"],
        )
    )
    assert len(target_container_registries) == 1
    target_container_registry = target_container_registries[0]

    query = """
            mutation ModifyContainerRegistry($id: String!, $props: ModifyContainerRegistryInput!) {
                modify_container_registry(id: $id, props: $props) {
                    container_registry {
                        $CONTAINER_REGISTRY_FIELDS
                    }
                }
            }
        """.replace("$CONTAINER_REGISTRY_FIELDS", CONTAINER_REGISTRY_FIELDS)

    # Given an empty string to password
    variables = {
        "id": target_container_registry["id"],
        "props": {
            "registry_name": "cr.example.com",
            "password": "",
        },
    }

    # Then password is set to empty string
    response = await client.execute_async(query, variables=variables, context_value=context)
    container_registry = response["data"]["modify_container_registry"]["container_registry"]
    assert container_registry["config"]["registry_name"] == "cr.example.com"
    assert container_registry["config"]["url"] == "http://cr2.example.com"
    assert container_registry["config"]["type"] == "harbor2"
    assert container_registry["config"]["project"] == "example"
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
        query ContainerRegistries($registry_name: String!) {
            container_registries (registry_name: $registry_name) {
                $CONTAINER_REGISTRY_FIELDS
            }
        }
        """.replace("$CONTAINER_REGISTRY_FIELDS", CONTAINER_REGISTRY_FIELDS)

    variables: dict[str, dict | str] = {
        "registry_name": "cr.example.com",
    }

    response = await client.execute_async(query, variables=variables, context_value=context)

    target_container_registries = list(
        filter(
            lambda item: item["config"]["project"] == "example",
            response["data"]["container_registries"],
        )
    )
    assert len(target_container_registries) == 1
    target_container_registry = target_container_registries[0]

    query = """
            mutation ModifyContainerRegistry($id: String!, $props: ModifyContainerRegistryInput!) {
                modify_container_registry(id: $id, props: $props) {
                    container_registry {
                        $CONTAINER_REGISTRY_FIELDS
                    }
                }
            }
        """.replace("$CONTAINER_REGISTRY_FIELDS", CONTAINER_REGISTRY_FIELDS)

    # Given a null to password
    variables = {
        "id": target_container_registry["id"],
        "props": {
            "registry_name": "cr.example.com",
            "password": None,
        },
    }

    # Then password is unset
    response = await client.execute_async(query, variables=variables, context_value=context)
    container_registry = response["data"]["modify_container_registry"]["container_registry"]
    assert container_registry["config"]["registry_name"] == "cr.example.com"
    assert container_registry["config"]["url"] == "http://cr2.example.com"
    assert container_registry["config"]["type"] == "harbor2"
    assert container_registry["config"]["project"] == "example"
    assert container_registry["config"]["username"] == "username2"
    assert container_registry["config"]["password"] is None
    assert container_registry["config"]["ssl_verify"] is False
    assert container_registry["config"]["is_global"] is False


@pytest.mark.dependency(depends=["test_modify_container_registry_allows_null_for_unset"])
@pytest.mark.asyncio
async def test_delete_container_registry(client: Client, database_engine: ExtendedAsyncSAEngine):
    context = get_graphquery_context(database_engine)

    query = """
        query ContainerRegistries($registry_name: String!) {
            container_registries (registry_name: $registry_name) {
                $CONTAINER_REGISTRY_FIELDS
            }
        }
        """.replace("$CONTAINER_REGISTRY_FIELDS", CONTAINER_REGISTRY_FIELDS)

    variables = {
        "registry_name": "cr.example.com",
    }

    response = await client.execute_async(query, variables=variables, context_value=context)

    target_container_registries = list(
        filter(
            lambda item: item["config"]["project"] == "example",
            response["data"]["container_registries"],
        )
    )
    assert len(target_container_registries) == 1
    target_container_registry = target_container_registries[0]

    query = """
            mutation DeleteContainerRegistry($id: String!) {
                delete_container_registry(id: $id) {
                    container_registry {
                        $CONTAINER_REGISTRY_FIELDS
                    }
                }
            }
        """.replace("$CONTAINER_REGISTRY_FIELDS", CONTAINER_REGISTRY_FIELDS)

    variables = {
        "id": target_container_registry["id"],
    }

    response = await client.execute_async(query, variables=variables, context_value=context)
    container_registry = response["data"]["delete_container_registry"]["container_registry"]
    assert container_registry["config"]["registry_name"] == "cr.example.com"

    query = """
        query ContainerRegistries($registry_name: String!) {
            container_registries (registry_name: $registry_name) {
                $CONTAINER_REGISTRY_FIELDS
            }
        }
        """.replace("$CONTAINER_REGISTRY_FIELDS", CONTAINER_REGISTRY_FIELDS)

    response = await client.execute_async(query, variables=variables, context_value=context)
    assert response["data"] is None
