from http import HTTPStatus

import pytest
import sqlalchemy as sa
from aioresponses import aioresponses
from graphene import Schema
from graphene.test import Client

from ai.backend.common.metrics.metric import GraphQLMetricObserver
from ai.backend.common.types import ResourceSlot, SlotName, SlotTypes, VFolderHostPermission
from ai.backend.common.utils import b64encode
from ai.backend.manager.api.context import RootContext
from ai.backend.manager.models.gql import GraphQueryContext, Mutation, Query
from ai.backend.manager.models.group import GroupRow, ProjectType
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.server import (
    database_ctx,
    services_ctx,
)
from ai.backend.testutils.extra_fixtures import FIXTURES_FOR_HARBOR_CRUD_TEST


@pytest.fixture(scope="module")
def client() -> Client:
    return Client(Schema(query=Query, mutation=Mutation, auto_camelcase=False))


def get_graphquery_context(
    database_engine: ExtendedAsyncSAEngine, services_ctx
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
        services_ctx=services_ctx,  # type: ignore
        metric_observer=GraphQLMetricObserver.instance(),
        processors=None,  # type: ignore
        scheduler_repository=None,  # type: ignore
        user_repository=None,  # type: ignore
        agent_repository=None,  # type: ignore
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("extra_fixtures", FIXTURES_FOR_HARBOR_CRUD_TEST)
async def test_harbor_read_project_quota(
    client: Client,
    mock_etcd_ctx,
    mock_config_provider_ctx,
    database_fixture,
    create_app_and_client,
):
    test_app, _ = await create_app_and_client(
        [
            mock_etcd_ctx,
            mock_config_provider_ctx,
            database_ctx,
            services_ctx,
        ],
        [],
    )

    root_ctx: RootContext = test_app["_root.context"]
    context = get_graphquery_context(root_ctx.db, root_ctx.services_ctx)

    # Arbitrary values for mocking Harbor API responses
    HARBOR_PROJECT_ID = "123"
    HARBOR_QUOTA_ID = 456
    HARBOR_QUOTA_VALUE = 1024

    with aioresponses() as mocked:
        get_project_id_url = "http://mock_registry/api/v2.0/projects/mock_project"
        mocked.get(
            get_project_id_url, status=HTTPStatus.OK, payload={"project_id": HARBOR_PROJECT_ID}
        )

        get_quota_url = f"http://mock_registry/api/v2.0/quotas?reference=project&reference_id={HARBOR_PROJECT_ID}"
        mocked.get(
            get_quota_url,
            status=HTTPStatus.OK,
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


async def test_default_value_types_correctly_processed(
    database_fixture,
    database_engine: ExtendedAsyncSAEngine,
) -> None:
    group_name = "test_group_default"
    minimum_required_data = {
        "name": group_name,
        "domain_name": "default",
        "resource_policy": "default",
    }
    async with database_engine.begin_session() as session:
        await session.execute(sa.insert(GroupRow).values(minimum_required_data))

        result = await session.scalar(sa.select(GroupRow).where(GroupRow.name == group_name))

        assert result.description is None
        assert result.is_active is True
        assert result.integration_id is None
        assert result.total_resource_slots == ResourceSlot.from_user_input({}, None)
        assert result.type == ProjectType.GENERAL
        assert result.container_registry == {}
        assert result.dotfiles == b"\x90"


async def test_db_data_insertion(
    database_fixture,
    database_engine: ExtendedAsyncSAEngine,
) -> None:
    group_name = "test_data_insertion"
    data = {
        "name": group_name,
        "description": "test description",
        "is_active": False,
        "integration_id": "test_integration_id",
        "domain_name": "default",
        "total_resource_slots": ResourceSlot.from_user_input(
            {"a": "1", "b": "2g"}, {SlotName("a"): SlotTypes.COUNT, SlotName("b"): SlotTypes.BYTES}
        ),
        "allowed_vfolder_hosts": {
            "local:volume1": [
                "create-vfolder",
            ]
        },
        "dotfiles": b"test_dotfiles",
        "resource_policy": "default",
        "type": ProjectType.MODEL_STORE,
        "container_registry": {
            "registry": "example_registry",
            "project": "example_project",
        },
    }

    async with database_engine.begin_session() as session:
        await session.execute(sa.insert(GroupRow).values(data))

        result = await session.scalar(sa.select(GroupRow).where(GroupRow.name == group_name))
        assert result.description == data["description"]
        assert result.is_active == data["is_active"]
        assert result.created_at is not None
        assert result.modified_at is not None
        assert result.integration_id == data["integration_id"]
        assert result.total_resource_slots == data["total_resource_slots"]
        assert result.allowed_vfolder_hosts == {"local:volume1": {VFolderHostPermission.CREATE}}
        assert result.resource_policy == data["resource_policy"]
        assert result.type == data["type"]
        assert result.container_registry == data["container_registry"]
        assert result.dotfiles == data["dotfiles"]
