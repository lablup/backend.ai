from unittest.mock import AsyncMock, MagicMock

import pytest
from graphene import Schema
from graphene.test import Client

from ai.backend.common.metrics.metric import GraphQLMetricObserver
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.config.unified import ManagerUnifiedConfig
from ai.backend.manager.defs import PASSWORD_PLACEHOLDER
from ai.backend.manager.models.container_registry import ContainerRegistryType
from ai.backend.manager.models.gql import GraphQueryContext, Mutation, Query
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.container_registry.repository import (
    ContainerRegistryRepository,
)
from ai.backend.manager.services.container_registry.processors import (
    ContainerRegistryProcessors,
)
from ai.backend.manager.services.container_registry.service import ContainerRegistryService
from ai.backend.manager.services.processors import Processors

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
    return Client(Schema(query=Query, mutation=Mutation, auto_camelcase=False))


@pytest.fixture
def container_registry_repository(
    database_engine: ExtendedAsyncSAEngine,
) -> ContainerRegistryRepository:
    return ContainerRegistryRepository(db=database_engine)


@pytest.fixture
def container_registry_service(
    container_registry_repository: ContainerRegistryRepository,
) -> ContainerRegistryService:
    return ContainerRegistryService(
        db=container_registry_repository._db,
        container_registry_repository=container_registry_repository,
        admin_container_registry_repository=MagicMock(),
    )


@pytest.fixture
def container_registry_processor(
    container_registry_service: ContainerRegistryService,
):
    return ContainerRegistryProcessors(
        service=container_registry_service,
        action_monitors=MagicMock(),
    )


@pytest.fixture
def processors(container_registry_processor: ContainerRegistryProcessors) -> Processors:
    processors = MagicMock(spec=Processors)
    processors.container_registry = container_registry_processor
    return processors


async def get_graphquery_context(
    database_engine: ExtendedAsyncSAEngine,
    unified_config: ManagerUnifiedConfig,
    processors: Processors,
) -> GraphQueryContext:
    mock_loader = MagicMock()
    mock_loader.load = AsyncMock()
    mock_loader.load.return_value = unified_config.model_dump()

    config_provider = await ManagerConfigProvider.create(
        loader=mock_loader,
        etcd_watcher=MagicMock(),
        legacy_etcd_config_loader=MagicMock(),  # type: ignore
    )
    return GraphQueryContext(
        schema=None,  # type: ignore
        dataloader_manager=None,  # type: ignore
        config_provider=config_provider,
        etcd=MagicMock(),  # type: ignore
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
        services_ctx=None,  # type: ignore
        metric_observer=GraphQLMetricObserver.instance(),
        processors=processors,
        scheduler_repository=None,  # type: ignore
        user_repository=None,  # type: ignore
        agent_repository=None,  # type: ignore
    )


@pytest.mark.dependency()
@pytest.mark.asyncio
async def test_create_container_registry(
    client: Client,
    database_engine: ExtendedAsyncSAEngine,
    unified_config: ManagerUnifiedConfig,
    processors: Processors,
):
    context = await get_graphquery_context(database_engine, unified_config, processors)

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
async def test_modify_container_registry(
    client: Client,
    database_engine: ExtendedAsyncSAEngine,
    unified_config: ManagerUnifiedConfig,
    processors: Processors,
):
    context = await get_graphquery_context(database_engine, unified_config, processors)

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
    print("response!!#W!#", response)

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
    client: Client,
    database_engine: ExtendedAsyncSAEngine,
    unified_config: ManagerUnifiedConfig,
    processors: Processors,
):
    context = await get_graphquery_context(database_engine, unified_config, processors)

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
    client: Client,
    database_engine: ExtendedAsyncSAEngine,
    unified_config: ManagerUnifiedConfig,
    processors: Processors,
):
    context = await get_graphquery_context(database_engine, unified_config, processors)

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
async def test_delete_container_registry(
    client: Client,
    database_engine: ExtendedAsyncSAEngine,
    unified_config: ManagerUnifiedConfig,
    processors: Processors,
):
    context = await get_graphquery_context(database_engine, unified_config, processors)

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
