import pytest
from graphene import Schema
from graphene.test import Client

from ai.backend.manager.models.gql import GraphQueryContext, Mutations, Queries
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.server import database_ctx


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
    extra_fixtures, client: Client, test_case, database_fixture, create_app_and_client
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
    extra_fixtures, client: Client, test_case, database_fixture, create_app_and_client
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
