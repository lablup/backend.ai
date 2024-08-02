import pytest
from graphene.test import Client

from ai.backend.manager.config import SharedConfig
from ai.backend.manager.defs import PASSWORD_PLACEHOLDER
from ai.backend.manager.models.gql import GraphQueryContext
from ai.backend.testutils.bootstrap import etcd_container  # noqa: F401

CONTAINER_REGISTRY_FIELDS = """
    container_registry {
        hostname
        config {
            url
            type
            project
            username
            password
            ssl_verify
        }
    }
"""


@pytest.fixture(scope="module")
def etcd_context(base_context, etcd_container) -> GraphQueryContext:  # noqa: F811
    shared_config = SharedConfig(
        etcd_addr=etcd_container[1],
        etcd_user="",
        etcd_password="",
        namespace="local",
    )
    superadmin_user = {"role": "superadmin"}
    return base_context(shared_config=shared_config, user=superadmin_user)

@pytest.mark.dependency()
@pytest.mark.asyncio
async def test_create_container_registry(client: Client, etcd_context: GraphQueryContext):
    query = """
        mutation CreateContainerRegistry($hostname: String!, $props: CreateContainerRegistryInput!) {
            create_container_registry(hostname: $hostname, props: $props) {
                $CONTAINER_REGISTRY_FIELDS
            }
        }
    """.replace("$CONTAINER_REGISTRY_FIELDS", CONTAINER_REGISTRY_FIELDS)

    variables = {
        "hostname": "cr.example.com",
        "props": {
            "url": "http://cr.example.com",
            "type": "dockerhub",
            "project": ["default"],
            "username": "username",
            "password": "password",
            "ssl_verify": False,
        },
    }

    response = await client.execute_async(query, variables=variables, context_value=etcd_context)
    container_registry = response["data"]["create_container_registry"]["container_registry"]
    assert container_registry["hostname"] == "cr.example.com"
    assert container_registry["config"] == {
        "url": "http://cr.example.com",
        "type": "dockerhub",
        "project": ["default"],
        "username": "username",
        "password": PASSWORD_PLACEHOLDER,
        "ssl_verify": False,
    }


@pytest.mark.dependency(depends=["test_create_container_registry"])
@pytest.mark.asyncio
async def test_modify_container_registry(client: Client, etcd_context: GraphQueryContext):
    query = """
        mutation ModifyContainerRegistry($hostname: String!, $props: ModifyContainerRegistryInput!) {
            modify_container_registry(hostname: $hostname, props: $props) {
                $CONTAINER_REGISTRY_FIELDS
            }
        }
    """.replace("$CONTAINER_REGISTRY_FIELDS", CONTAINER_REGISTRY_FIELDS)

    variables = {
        "hostname": "cr.example.com",
        "props": {
            "username": "username2",
        },
    }

    response = await client.execute_async(query, variables=variables, context_value=etcd_context)
    print(response)
    container_registry = response["data"]["modify_container_registry"]["container_registry"]
    assert container_registry["hostname"] == "cr.example.com"
    assert container_registry["config"]["url"] == "http://cr.example.com"
    assert container_registry["config"]["type"] == "dockerhub"
    assert container_registry["config"]["project"] == ["default"]
    assert container_registry["config"]["username"] == "username2"
    assert container_registry["config"]["ssl_verify"] is False

    variables = {
        "hostname": "cr.example.com",
        "props": {
            "url": "http://cr2.example.com",
            "type": "harbor2",
            "project": ["default", "example"],
        },
    }

    response = await client.execute_async(query, variables=variables, context_value=etcd_context)
    container_registry = response["data"]["modify_container_registry"]["container_registry"]
    assert container_registry["hostname"] == "cr.example.com"
    assert container_registry["config"]["url"] == "http://cr2.example.com"
    assert container_registry["config"]["type"] == "harbor2"
    assert container_registry["config"]["project"] == ["default", "example"]
    assert container_registry["config"]["username"] == "username2"
    assert container_registry["config"]["ssl_verify"] is False


@pytest.mark.dependency(depends=["test_modify_container_registry"])
@pytest.mark.asyncio
async def test_modify_container_registry_allows_empty_string(
    client: Client, etcd_context: GraphQueryContext
):
    query = """
        mutation ModifyContainerRegistry($hostname: String!, $props: ModifyContainerRegistryInput!) {
            modify_container_registry(hostname: $hostname, props: $props) {
                $CONTAINER_REGISTRY_FIELDS
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
    response = await client.execute_async(query, variables=variables, context_value=etcd_context)
    container_registry = response["data"]["modify_container_registry"]["container_registry"]
    assert container_registry["hostname"] == "cr.example.com"
    assert container_registry["config"]["url"] == "http://cr2.example.com"
    assert container_registry["config"]["type"] == "harbor2"
    assert container_registry["config"]["project"] == ["default", "example"]
    assert container_registry["config"]["username"] == "username2"
    assert container_registry["config"]["ssl_verify"] is False

    # Direct access to the etcd to reveal that the password is actually set as an empty string
    raw_container_registry = await etcd_context.shared_config.get_container_registry(
        "cr.example.com"
    )
    assert raw_container_registry["password"] == ""


@pytest.mark.dependency(depends=["test_modify_container_registry_allows_empty_string"])
@pytest.mark.asyncio
async def test_modify_container_registry_allows_null_for_unset(
    client: Client, etcd_context: GraphQueryContext
):
    query = """
        mutation ModifyContainerRegistry($hostname: String!, $props: ModifyContainerRegistryInput!) {
            modify_container_registry(hostname: $hostname, props: $props) {
                $CONTAINER_REGISTRY_FIELDS
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
    response = await client.execute_async(query, variables=variables, context_value=etcd_context)
    container_registry = response["data"]["modify_container_registry"]["container_registry"]
    assert container_registry["hostname"] == "cr.example.com"
    assert container_registry["config"]["url"] == "http://cr2.example.com"
    assert container_registry["config"]["type"] == "harbor2"
    assert container_registry["config"]["project"] == ["default", "example"]
    assert container_registry["config"]["username"] == "username2"
    assert container_registry["config"]["password"] is None
    assert container_registry["config"]["ssl_verify"] is False


@pytest.mark.dependency(depends=["test_modify_container_registry_allows_null_for_unset"])
@pytest.mark.asyncio
async def test_delete_container_registry(client: Client, etcd_context: GraphQueryContext):
    query = """
        mutation DeleteContainerRegistry($hostname: String!) {
            delete_container_registry(hostname: $hostname) {
                $CONTAINER_REGISTRY_FIELDS
            }
        }
    """.replace("$CONTAINER_REGISTRY_FIELDS", CONTAINER_REGISTRY_FIELDS)

    variables = {
        "hostname": "cr.example.com",
    }

    response = await client.execute_async(query, variables=variables, context_value=etcd_context)
    container_registry = response["data"]["delete_container_registry"]["container_registry"]
    assert container_registry["hostname"] == "cr.example.com"

    query = """
        query ContainerRegistry($hostname: String!) {
            container_registry(hostname: $hostname) {
                $CONTAINER_REGISTRY_FIELDS
            }
        }
    """.replace("$CONTAINER_REGISTRY_FIELDS", CONTAINER_REGISTRY_FIELDS)

    response = await client.execute_async(query, variables=variables, context_value=etcd_context)
    assert response["data"] is None
