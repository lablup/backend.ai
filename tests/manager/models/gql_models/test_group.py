import pytest
from aioresponses import aioresponses
from graphene import Schema
from graphene.test import Client

from ai.backend.common.utils import b64encode
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
        network_plugin_ctx=None,  # type: ignore
        services_ctx=None,  # type: ignore
    )


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
