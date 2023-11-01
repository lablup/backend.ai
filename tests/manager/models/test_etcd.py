import pytest
from graphene import Schema
from graphene.test import Client

from ai.backend.client.session import APIConfig, Session
from ai.backend.manager.models.gql import Mutations, Queries

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

SCHEMA = Schema(query=Queries, mutation=Mutations, auto_camelcase=False)


def _admin_session():
    api_config = APIConfig(
        endpoint="http://127.0.0.1:8091",
        endpoint_type="api",
        access_key="AKIAIOSFODNN7EXAMPLE",
        secret_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
        skip_sslcert_validation=True,
    )
    return Session(config=api_config)


@pytest.mark.dependency()
@pytest.mark.asyncio
async def test_create_container_registry():
    client = Client(SCHEMA)
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
            "type": "harbor2",
            "project": ["default"],
            "username": "username",
            "password": "password",
            "ssl_verify": False,
        },
    }

    context = {}  # info.context
    response = await client.execute_async(query, variables=variables, context_value=context)
    print(response)  # {'data': {'create_container_registry': {'container_registry': None}}}
    assert response is None

    return

    with _admin_session() as sess:
        response = sess.Admin.query(query=query, variables=variables)
        container_registry = response["create_container_registry"]["container_registry"]
        assert container_registry["hostname"] == "cr.example.com"
        assert container_registry["config"] == {
            "url": "http://cr.example.com",
            "type": "harbor2",
            "project": ["default"],
            "username": "username",
            "password": "*****",
            "ssl_verify": False,
        }


@pytest.mark.dependency(depends=["test_create_container_registry"])
def test_modify_container_registry():
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

    # response = CLIENT.execute(query, variables=variables)
    # print(response)  # {'data': {'modify_container_registry': {'container_registry': None}}}

    # assert response["config"]["url"] != "http://cr.example.com"

    with _admin_session() as sess:
        response = sess.Admin.query(query=query, variables=variables)
        container_registry = response["modify_container_registry"]["container_registry"]
        assert container_registry["config"]["url"] == "http://cr.example.com"
        assert container_registry["config"]["type"] == "harbor2"
        assert container_registry["config"]["project"] == ["default"]
        assert container_registry["config"]["username"] == "username2"
        assert container_registry["config"]["ssl_verify"] is False


@pytest.mark.dependency(depends=["test_modify_container_registry"])
def test_modify_container_registry_allows_empty_string():
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
            "password": "",
        },
    }

    with _admin_session() as sess:
        response = sess.Admin.query(query=query, variables=variables)
        container_registry = response["modify_container_registry"]["container_registry"]
        assert container_registry["config"]["url"] == "http://cr.example.com"
        assert container_registry["config"]["type"] == "harbor2"
        assert container_registry["config"]["project"] == ["default"]
        # assert container_registry["config"]["username"] == "username2"
        assert container_registry["config"]["password"] == "*****"
        assert container_registry["config"]["ssl_verify"] is False


@pytest.mark.dependency(depends=["test_modify_container_registry_allows_empty_string"])
def test_modify_container_registry_allows_null_for_unset():
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
            "password": None,
        },
    }

    with _admin_session() as sess:
        response = sess.Admin.query(query=query, variables=variables)
        container_registry = response["modify_container_registry"]["container_registry"]
        assert container_registry["config"]["url"] == "http://cr.example.com"
        assert container_registry["config"]["type"] == "harbor2"
        assert container_registry["config"]["project"] == ["default"]
        # assert container_registry["config"]["username"] == "username2"
        assert container_registry["config"]["password"] is None
        assert container_registry["config"]["ssl_verify"] is False


@pytest.mark.dependency(depends=["test_modify_container_registry_allows_null_for_unset"])
def test_delete_container_registry():
    query = """
        mutation DeleteContainerRegistry($hostname: String!) {
            delete_container_registry(hostname: $hostname) {
                $CONTAINER_REGISTRY_FIELDS
            }
        }
    """.replace("$CONTAINER_REGISTRY_FIELDS", CONTAINER_REGISTRY_FIELDS)

    with _admin_session() as sess:
        response = sess.Admin.query(query=query, variables={"hostname": "cr.example.com"})
        container_registry = response["delete_container_registry"]["container_registry"]
        assert container_registry["hostname"] == "cr.example.com"
