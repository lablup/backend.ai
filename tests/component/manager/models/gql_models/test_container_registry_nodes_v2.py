from unittest.mock import MagicMock

import pytest
from graphene import Schema
from graphene.test import Client

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.common.metrics.metric import GraphQLMetricObserver
from ai.backend.manager.defs import PASSWORD_PLACEHOLDER
from ai.backend.manager.models.gql import GraphQueryContext, Mutation, Query
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.container_registry.admin_repository import (
    AdminContainerRegistryRepository,
)
from ai.backend.manager.repositories.container_registry.repository import (
    ContainerRegistryRepository,
)
from ai.backend.manager.server import database_ctx
from ai.backend.manager.services.container_registry.processors import ContainerRegistryProcessors
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


@pytest.fixture(scope="module")
def client() -> Client:
    return Client(Schema(query=Query, mutation=Mutation, auto_camelcase=False))


@pytest.fixture
def container_registry_processor(
    extra_fixtures, database_fixture, database_engine
) -> ContainerRegistryProcessors:
    repository = ContainerRegistryRepository(
        db=database_engine,
    )
    admin_repository = AdminContainerRegistryRepository(
        db=database_engine,
    )
    container_registry_service = ContainerRegistryService(
        db=database_engine,
        container_registry_repository=repository,
        admin_container_registry_repository=admin_repository,
    )
    return ContainerRegistryProcessors(container_registry_service, [])


@pytest.fixture
def processors(container_registry_processor) -> Processors:
    mock_processors = MagicMock(spec=Processors)
    mock_processors.container_registry = container_registry_processor
    return mock_processors


def get_graphquery_context(
    database_engine: ExtendedAsyncSAEngine, processors: Processors
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
    client: Client, database_engine: ExtendedAsyncSAEngine, processors: Processors
):
    context = get_graphquery_context(database_engine, processors)

    query = """
            mutation ($props: CreateContainerRegistryNodeInputV2!) {
                create_container_registry_node_v2(props: $props) {
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
            "type": ContainerRegistryType.DOCKER,
            "project": "default",
            "username": "username",
            "password": "password",
            "ssl_verify": False,
            "is_global": False,
        }
    }

    response = await client.execute_async(query, variables=variables, context_value=context)
    container_registry = response["data"]["create_container_registry_node_v2"]["container_registry"]

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

    variables["props"]["project"] = "default2"
    await client.execute_async(query, variables=variables, context_value=context)


@pytest.mark.dependency(depends=["test_create_container_registry_v2"])
@pytest.mark.asyncio
async def test_modify_container_registry(
    client: Client, database_engine: ExtendedAsyncSAEngine, processors: Processors
):
    context = get_graphquery_context(database_engine, processors)

    query = """
        query ($filter: String!) {
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
            lambda item: item["node"]["project"] == "default",
            response["data"]["container_registry_nodes"]["edges"],
        )
    )

    assert len(target_container_registries) == 1
    target_container_registry = target_container_registries[0]["node"]

    query = """
            mutation ($id: String!, $props: ModifyContainerRegistryNodeInputV2!) {
                modify_container_registry_node_v2(id: $id, props: $props) {
                    container_registry {
                        $CONTAINER_REGISTRY_FIELDS
                    }
                }
            }
        """.replace("$CONTAINER_REGISTRY_FIELDS", CONTAINER_REGISTRY_FIELDS)

    variables = {
        "id": target_container_registry["row_id"],
        "props": {
            "registry_name": "cr.example.com",
            "username": "username2",
        },
    }

    response = await client.execute_async(query, variables=variables, context_value=context)

    container_registry = response["data"]["modify_container_registry_node_v2"]["container_registry"]
    assert container_registry["registry_name"] == "cr.example.com"
    assert container_registry["url"] == "http://cr.example.com"
    assert container_registry["type"] == "docker"
    assert container_registry["project"] == "default"
    assert container_registry["username"] == "username2"
    assert container_registry["ssl_verify"] is False
    assert container_registry["is_global"] is False

    variables = {
        "id": target_container_registry["row_id"],
        "props": {
            "registry_name": "cr.example.com",
            "url": "http://cr2.example.com",
            "type": ContainerRegistryType.HARBOR2,
            "project": "example",
        },
    }

    response = await client.execute_async(query, variables=variables, context_value=context)

    container_registry = response["data"]["modify_container_registry_node_v2"]["container_registry"]

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
    client: Client, database_engine: ExtendedAsyncSAEngine, processors: Processors
):
    context = get_graphquery_context(database_engine, processors)

    query = """
        query ($filter: String!) {
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
            mutation ($id: String!, $props: ModifyContainerRegistryNodeInputV2!) {
                modify_container_registry_node_v2(id: $id, props: $props) {
                    container_registry {
                        $CONTAINER_REGISTRY_FIELDS
                    }
                }
            }
        """.replace("$CONTAINER_REGISTRY_FIELDS", CONTAINER_REGISTRY_FIELDS)

    # Given an empty string to password
    variables = {
        "id": target_container_registry["row_id"],
        "props": {
            "registry_name": "cr.example.com",
            "password": "",
        },
    }

    # Then password is set to empty string
    response = await client.execute_async(query, variables=variables, context_value=context)

    container_registry = response["data"]["modify_container_registry_node_v2"]["container_registry"]
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
    client: Client, database_engine: ExtendedAsyncSAEngine, processors: Processors
):
    context = get_graphquery_context(database_engine, processors)

    query = """
        query ($filter: String!) {
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
            mutation ($id: String!, $props: ModifyContainerRegistryNodeInputV2!) {
                modify_container_registry_node_v2(id: $id, props: $props) {
                    container_registry {
                        $CONTAINER_REGISTRY_FIELDS
                    }
                }
            }
        """.replace("$CONTAINER_REGISTRY_FIELDS", CONTAINER_REGISTRY_FIELDS)

    # Given a null to password
    variables = {
        "id": target_container_registry["row_id"],
        "props": {
            "registry_name": "cr.example.com",
            "password": None,
        },
    }

    # Then password is unset
    response = await client.execute_async(query, variables=variables, context_value=context)
    container_registry = response["data"]["modify_container_registry_node_v2"]["container_registry"]
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
    client: Client, database_engine: ExtendedAsyncSAEngine, processors: Processors
):
    context = get_graphquery_context(database_engine, processors)

    query = """
        query ($filter: String!) {
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
            mutation ($id: String!) {
                delete_container_registry_node_v2(id: $id) {
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

    container_registry = response["data"]["delete_container_registry_node_v2"]["container_registry"]
    assert container_registry["registry_name"] == "cr.example.com"

    query = """
        query ($filter: String!) {
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
    client: Client,
    mock_etcd_ctx,
    mock_config_provider_ctx,
    database_fixture,
    extra_fixtures,
    test_case,
    create_app_and_client,
    processors,
):
    test_app, _ = await create_app_and_client(
        [
            mock_etcd_ctx,
            mock_config_provider_ctx,
            database_ctx,
        ],
        [],
    )

    root_ctx = test_app["_root.context"]
    context = get_graphquery_context(root_ctx.db, processors)

    query = """
        mutation ($id: String!, $props: ModifyContainerRegistryNodeInputV2!) {
            modify_container_registry_node_v2(id: $id, props: $props) {
                container_registry {
                    $CONTAINER_REGISTRY_FIELDS
                }
            }
        }
        """.replace("$CONTAINER_REGISTRY_FIELDS", CONTAINER_REGISTRY_FIELDS)

    variables = {
        "id": test_case["registry_id"],
        "props": {
            "allowed_groups": {
                "add": [test_case["group_id"]],
            }
        },
    }

    response = await client.execute_async(query, variables=variables, context_value=context)
    already_associated = "association_container_registries_groups" in extra_fixtures

    if already_associated:
        assert response["data"]["modify_container_registry_node_v2"] is None
        assert response["errors"] is not None
    else:
        assert (
            response["data"]["modify_container_registry_node_v2"]["container_registry"][
                "registry_name"
            ]
            == "mock_registry"
        )


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
    client: Client,
    mock_etcd_ctx,
    mock_config_provider_ctx,
    database_fixture,
    extra_fixtures,
    test_case,
    create_app_and_client,
    processors,
):
    test_app, _ = await create_app_and_client(
        [
            mock_etcd_ctx,
            mock_config_provider_ctx,
            database_ctx,
        ],
        [],
    )

    root_ctx = test_app["_root.context"]
    context = get_graphquery_context(root_ctx.db, processors)

    query = """
        mutation ($id: String!, $props: ModifyContainerRegistryNodeInputV2!) {
            modify_container_registry_node_v2(id: $id, props: $props) {
                container_registry {
                    $CONTAINER_REGISTRY_FIELDS
                }
            }
        }
        """.replace("$CONTAINER_REGISTRY_FIELDS", CONTAINER_REGISTRY_FIELDS)

    variables = {
        "id": test_case["registry_id"],
        "props": {
            "allowed_groups": {
                "remove": [test_case["group_id"]],
            }
        },
    }

    response = await client.execute_async(query, variables=variables, context_value=context)
    association_exist = "association_container_registries_groups" in extra_fixtures

    if association_exist:
        assert (
            response["data"]["modify_container_registry_node_v2"]["container_registry"][
                "registry_name"
            ]
            == "mock_registry"
        )
    else:
        assert response["data"]["modify_container_registry_node_v2"] is None
        assert response["errors"] is not None
