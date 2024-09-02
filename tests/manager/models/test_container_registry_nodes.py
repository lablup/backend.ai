from unittest.mock import MagicMock

import pytest
from graphene import Schema
from graphene.test import Client

from ai.backend.manager.defs import PASSWORD_PLACEHOLDER
from ai.backend.manager.models.container_registry import ContainerRegistryType
from ai.backend.manager.models.gql import GraphQueryContext, Mutations, Queries
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

CONTAINER_REGISTRY_FIELDS = """
    row_id
    registry_name
    url
    type
    project
    username
    password
    ssl_verify
    is_global
"""


@pytest.fixture(scope="module")
def client() -> Client:
    return Client(Schema(query=Queries, mutation=Mutations, auto_camelcase=False))


def get_graphquery_context(database_engine: ExtendedAsyncSAEngine) -> GraphQueryContext:
    mock_shared_config = MagicMock()
    mock_shared_config_api_mock = MagicMock()

    def mock_shared_config_getitem(key):
        if key == "api":
            return mock_shared_config_api_mock
        else:
            return None

    def mock_shared_config_api_getitem(key):
        if key == "max-gql-connection-page-size":
            return None
        else:
            return MagicMock()

    mock_shared_config.__getitem__.side_effect = mock_shared_config_getitem
    mock_shared_config_api_mock.__getitem__.side_effect = mock_shared_config_api_getitem

    return GraphQueryContext(
        schema=None,  # type: ignore
        dataloader_manager=None,  # type: ignore
        local_config=None,  # type: ignore
        shared_config=mock_shared_config,  # type: ignore
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
            mutation CreateContainerRegistryNode($type: ContainerRegistryTypeField!, $registry_name: String!, $url: String!, $project: String!, $username: String!, $password: String!, $ssl_verify: Boolean!, $is_global: Boolean!) {
                create_container_registry_node(type: $type, registry_name: $registry_name, url: $url, project: $project, username: $username, password: $password, ssl_verify: $ssl_verify, is_global: $is_global) {
                    container_registry {
                        $CONTAINER_REGISTRY_FIELDS
                    }
                }
            }
        """.replace("$CONTAINER_REGISTRY_FIELDS", CONTAINER_REGISTRY_FIELDS)

    variables = {
        "registry_name": "cr.example.com",
        "url": "http://cr.example.com",
        "type": ContainerRegistryType.DOCKER,
        "project": "default",
        "username": "username",
        "password": "password",
        "ssl_verify": False,
        "is_global": False,
    }

    response = await client.execute_async(query, variables=variables, context_value=context)

    container_registry = response["data"]["create_container_registry_node"]["container_registry"]

    id = container_registry.pop("row_id", None)
    assert id is not None

    assert container_registry == {
        "registry_name": "cr.example.com",
        "url": "http://cr.example.com",
        "type": "docker",
        "project": "default",
        "username": "username",
        "password": PASSWORD_PLACEHOLDER,
        "ssl_verify": False,
        "is_global": False,
    }

    variables["project"] = "default2"
    await client.execute_async(query, variables=variables, context_value=context)


@pytest.mark.dependency(depends=["test_create_container_registry"])
@pytest.mark.asyncio
async def test_modify_container_registry(client: Client, database_engine: ExtendedAsyncSAEngine):
    context = get_graphquery_context(database_engine)

    query = """
        query ContainerRegistryNodes($filter: String!) {
            container_registry_nodes (filter: $filter) {
                edges {
                    node {
                        $CONTAINER_REGISTRY_FIELDS
                    }
                    cursor
                }
            }
        }
        """.replace("$CONTAINER_REGISTRY_FIELDS", CONTAINER_REGISTRY_FIELDS)

    variables: dict[str, dict | str] = {
        "filter": 'registry_name == "cr.example.com"',
    }

    response = await client.execute_async(query, variables=variables, context_value=context)
    print("response 1!!", response)

    target_container_registries = list(
        filter(
            lambda item: item["node"]["project"] == "default",
            response["data"]["container_registry_nodes"]["edges"],
        )
    )

    assert len(target_container_registries) == 1
    target_container_registry = target_container_registries[0]["node"]

    query = """
            mutation ModifyContainerRegistryNode($id: String!, $type: ContainerRegistryTypeField, $registry_name: String, $url: String, $project: String, $username: String, $password: String, $ssl_verify: Boolean, $is_global: Boolean) {
                modify_container_registry_node(id: $id, type: $type, registry_name: $registry_name, url: $url, project: $project, username: $username, password: $password, ssl_verify: $ssl_verify, is_global: $is_global) {
                    container_registry {
                        $CONTAINER_REGISTRY_FIELDS
                    }
                }
            }
        """.replace("$CONTAINER_REGISTRY_FIELDS", CONTAINER_REGISTRY_FIELDS)

    variables = {
        "id": target_container_registry["row_id"],
        "registry_name": "cr.example.com",
        "username": "username2",
    }

    response = await client.execute_async(query, variables=variables, context_value=context)

    container_registry = response["data"]["modify_container_registry_node"]["container_registry"]
    assert container_registry["registry_name"] == "cr.example.com"
    assert container_registry["url"] == "http://cr.example.com"
    assert container_registry["type"] == "docker"
    assert container_registry["project"] == "default"
    assert container_registry["username"] == "username2"
    assert container_registry["ssl_verify"] is False
    assert container_registry["is_global"] is False

    variables = {
        "id": target_container_registry["row_id"],
        "registry_name": "cr.example.com",
        "url": "http://cr2.example.com",
        "type": ContainerRegistryType.HARBOR2,
        "project": "example",
    }

    response = await client.execute_async(query, variables=variables, context_value=context)

    container_registry = response["data"]["modify_container_registry_node"]["container_registry"]

    assert container_registry["registry_name"] == "cr.example.com"
    assert container_registry["url"] == "http://cr2.example.com"
    assert container_registry["type"] == ContainerRegistryType.HARBOR2
    assert container_registry["project"] == "example"
    assert container_registry["username"] == "username2"
    assert container_registry["ssl_verify"] is False
    assert container_registry["is_global"] is False


@pytest.mark.dependency(depends=["test_modify_container_registry"])
@pytest.mark.asyncio
async def test_modify_container_registry_allows_empty_string(
    client: Client, database_engine: ExtendedAsyncSAEngine
):
    context = get_graphquery_context(database_engine)

    query = """
        query ContainerRegistryNodes($filter: String!) {
            container_registry_nodes (filter: $filter) {
                edges {
                    node {
                        $CONTAINER_REGISTRY_FIELDS
                    }
                    cursor
                }
            }
        }
        """.replace("$CONTAINER_REGISTRY_FIELDS", CONTAINER_REGISTRY_FIELDS)

    variables: dict[str, dict | str] = {
        "filter": 'registry_name == "cr.example.com"',
    }

    response = await client.execute_async(query, variables=variables, context_value=context)
    target_container_registries = list(
        filter(
            lambda item: item["node"]["project"] == "example",
            response["data"]["container_registry_nodes"]["edges"],
        )
    )
    assert len(target_container_registries) == 1
    target_container_registry = target_container_registries[0]["node"]

    query = """
            mutation ModifyContainerRegistryNode($id: String!, $type: ContainerRegistryTypeField, $registry_name: String, $url: String, $project: String, $username: String, $password: String, $ssl_verify: Boolean, $is_global: Boolean) {
                modify_container_registry_node(id: $id, type: $type, registry_name: $registry_name, url: $url, project: $project, username: $username, password: $password, ssl_verify: $ssl_verify, is_global: $is_global) {
                    container_registry {
                        $CONTAINER_REGISTRY_FIELDS
                    }
                }
            }
        """.replace("$CONTAINER_REGISTRY_FIELDS", CONTAINER_REGISTRY_FIELDS)

    # Given an empty string to password
    variables = {
        "id": target_container_registry["row_id"],
        "registry_name": "cr.example.com",
        "password": "",
    }

    # Then password is set to empty string
    response = await client.execute_async(query, variables=variables, context_value=context)

    container_registry = response["data"]["modify_container_registry_node"]["container_registry"]
    assert container_registry["registry_name"] == "cr.example.com"
    assert container_registry["url"] == "http://cr2.example.com"
    assert container_registry["type"] == ContainerRegistryType.HARBOR2
    assert container_registry["project"] == "example"
    assert container_registry["username"] == "username2"
    assert container_registry["password"] == PASSWORD_PLACEHOLDER
    assert container_registry["ssl_verify"] is False
    assert container_registry["is_global"] is False


@pytest.mark.dependency(depends=["test_modify_container_registry_allows_empty_string"])
@pytest.mark.asyncio
async def test_modify_container_registry_allows_null_for_unset(
    client: Client, database_engine: ExtendedAsyncSAEngine
):
    context = get_graphquery_context(database_engine)

    query = """
        query ContainerRegistryNodes($filter: String!) {
            container_registry_nodes (filter: $filter) {
                edges {
                    node {
                        $CONTAINER_REGISTRY_FIELDS
                    }
                    cursor
                }
            }
        }
        """.replace("$CONTAINER_REGISTRY_FIELDS", CONTAINER_REGISTRY_FIELDS)

    variables: dict[str, str | None] = {
        "filter": 'registry_name == "cr.example.com"',
    }

    response = await client.execute_async(query, variables=variables, context_value=context)

    target_container_registries = list(
        filter(
            lambda item: item["node"]["project"] == "example",
            response["data"]["container_registry_nodes"]["edges"],
        )
    )
    assert len(target_container_registries) == 1
    target_container_registry = target_container_registries[0]["node"]

    query = """
            mutation ModifyContainerRegistryNode($id: String!, $type: ContainerRegistryTypeField, $registry_name: String, $url: String, $project: String, $username: String, $password: String, $ssl_verify: Boolean, $is_global: Boolean) {
                modify_container_registry_node(id: $id, type: $type, registry_name: $registry_name, url: $url, project: $project, username: $username, password: $password, ssl_verify: $ssl_verify, is_global: $is_global) {
                    container_registry {
                        $CONTAINER_REGISTRY_FIELDS
                    }
                }
            }
        """.replace("$CONTAINER_REGISTRY_FIELDS", CONTAINER_REGISTRY_FIELDS)

    # Given a null to password
    variables = {
        "id": target_container_registry["row_id"],
        "registry_name": "cr.example.com",
        "password": None,
    }

    # Then password is unset
    response = await client.execute_async(query, variables=variables, context_value=context)
    container_registry = response["data"]["modify_container_registry_node"]["container_registry"]
    assert container_registry["registry_name"] == "cr.example.com"
    assert container_registry["url"] == "http://cr2.example.com"
    assert container_registry["type"] == ContainerRegistryType.HARBOR2
    assert container_registry["project"] == "example"
    assert container_registry["username"] == "username2"
    assert container_registry["password"] is None
    assert container_registry["ssl_verify"] is False
    assert container_registry["is_global"] is False


@pytest.mark.dependency(depends=["test_modify_container_registry_allows_null_for_unset"])
@pytest.mark.asyncio
async def test_delete_container_registry(client: Client, database_engine: ExtendedAsyncSAEngine):
    context = get_graphquery_context(database_engine)

    query = """
        query ContainerRegistryNodes($filter: String!) {
            container_registry_nodes (filter: $filter) {
                edges {
                    node {
                        $CONTAINER_REGISTRY_FIELDS
                    }
                    cursor
                }
            }
        }
        """.replace("$CONTAINER_REGISTRY_FIELDS", CONTAINER_REGISTRY_FIELDS)

    variables = {
        "filter": 'registry_name == "cr.example.com"',
    }

    response = await client.execute_async(query, variables=variables, context_value=context)

    target_container_registries = list(
        filter(
            lambda item: item["node"]["project"] == "example",
            response["data"]["container_registry_nodes"]["edges"],
        )
    )
    assert len(target_container_registries) == 1
    target_container_registry = target_container_registries[0]["node"]

    query = """
            mutation DeleteContainerRegistryNode($id: String!) {
                delete_container_registry_node(id: $id) {
                    container_registry {
                        $CONTAINER_REGISTRY_FIELDS
                    }
                }
            }
        """.replace("$CONTAINER_REGISTRY_FIELDS", CONTAINER_REGISTRY_FIELDS)

    variables = {
        "id": str(target_container_registry["row_id"]),
    }
    response = await client.execute_async(query, variables=variables, context_value=context)

    container_registry = response["data"]["delete_container_registry_node"]["container_registry"]
    assert container_registry["registry_name"] == "cr.example.com"

    query = """
        query ContainerRegistryNodes($filter: String!) {
            container_registry_nodes (filter: $filter) {
                edges {
                    node {
                        $CONTAINER_REGISTRY_FIELDS
                    }
                    cursor
                }
            }
        }
        """.replace("$CONTAINER_REGISTRY_FIELDS", CONTAINER_REGISTRY_FIELDS)

    variables = {
        "filter": f'row_id == "${target_container_registry["row_id"]}"',
    }

    response = await client.execute_async(query, variables=variables, context_value=context)
    assert response["data"]["container_registry_nodes"] is None
