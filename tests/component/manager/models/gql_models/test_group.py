from typing import Any

import pytest
import sqlalchemy as sa
from graphene import Schema
from graphene.test import Client

from ai.backend.common.metrics.metric import GraphQLMetricObserver
from ai.backend.common.types import ResourceSlot, SlotName, SlotTypes, VFolderHostPermission
from ai.backend.manager.api.gql_legacy.schema import GraphQueryContext, Mutation, Query
from ai.backend.manager.models.group import GroupRow, ProjectType
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.extra_fixtures import FIXTURES_FOR_HARBOR_CRUD_TEST

# TODO: test_harbor_read_project_quota requires services_ctx (harbor quota
# service) which is not yet available through the new ModuleDeps / database_engine
# pattern.  It needs to be refactored to inject the quota service directly.


@pytest.fixture(scope="module")
def client() -> Client:
    return Client(Schema(query=Query, mutation=Mutation, auto_camelcase=False))


def get_graphquery_context(
    database_engine: ExtendedAsyncSAEngine, services_ctx: Any
) -> GraphQueryContext:
    return GraphQueryContext(
        schema=None,
        dataloader_manager=None,  # type: ignore
        config_provider=None,  # type: ignore
        etcd=None,  # type: ignore
        user={"domain": "default", "role": "superadmin"},
        access_key="AKIAIOSFODNN7EXAMPLE",
        db=database_engine,
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
        services_ctx=services_ctx,
        metric_observer=GraphQLMetricObserver.instance(),
        processors=None,  # type: ignore
        scheduler_repository=None,  # type: ignore
        user_repository=None,  # type: ignore
        agent_repository=None,  # type: ignore
    )


@pytest.mark.skip(
    reason="Needs services_ctx (harbor quota service) -- not available via ModuleDeps yet"
)
@pytest.mark.parametrize("extra_fixtures", FIXTURES_FOR_HARBOR_CRUD_TEST, indirect=True)
async def test_harbor_read_project_quota(
    client: Client,
    database_fixture: None,
    database_engine: ExtendedAsyncSAEngine,
) -> None:
    # Requires services_ctx to provide harbor quota service
    pass


async def test_default_value_types_correctly_processed(
    database_fixture: None,
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
        assert result is not None

        assert result.description is None
        assert result.is_active is True
        assert result.integration_id is None
        assert result.total_resource_slots == ResourceSlot.from_user_input({}, None)
        assert result.type == ProjectType.GENERAL
        assert result.container_registry == {}
        assert result.dotfiles == b"\x90"


async def test_db_data_insertion(
    database_fixture: None,
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
        assert result is not None
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
