import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, AsyncGenerator, Optional
from unittest.mock import AsyncMock, MagicMock

import pytest
import sqlalchemy as sa

from ai.backend.common.exception import InvalidAPIParameters
from ai.backend.common.types import RedisConnectionInfo, ResourceSlot, VFolderHostPermissionMap
from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.data.group.types import GroupData, GroupModifier
from ai.backend.manager.errors.resource import ProjectNotFound
from ai.backend.manager.models.group import GroupRow, ProjectType
from ai.backend.manager.models.storage import StorageSessionManager
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.repositories.group.admin_repository import AdminGroupRepository
from ai.backend.manager.repositories.group.creators import GroupCreatorSpec
from ai.backend.manager.repositories.group.repositories import GroupRepositories
from ai.backend.manager.repositories.group.repository import GroupRepository
from ai.backend.manager.services.group.actions.create_group import (
    CreateGroupAction,
    CreateGroupActionResult,
)
from ai.backend.manager.services.group.actions.delete_group import (
    DeleteGroupAction,
    DeleteGroupActionResult,
)
from ai.backend.manager.services.group.actions.modify_group import (
    ModifyGroupAction,
    ModifyGroupActionResult,
)
from ai.backend.manager.services.group.actions.purge_group import (
    PurgeGroupAction,
)
from ai.backend.manager.services.group.processors import GroupProcessors
from ai.backend.manager.services.group.service import GroupService
from ai.backend.manager.types import OptionalState, TriState

from .utils import ScenarioBase


@pytest.fixture
def service_mock_args():
    return {
        "storage_manager": MagicMock(spec=StorageSessionManager),
        "config_provider": MagicMock(),
        "valkey_stat_client": MagicMock(spec=RedisConnectionInfo),
    }


@pytest.fixture
def mock_action_monitor() -> ActionMonitor:
    return MagicMock(spec=ActionMonitor)


@pytest.fixture
def processors(
    database_fixture, database_engine, service_mock_args, mock_action_monitor
) -> GroupProcessors:
    group_repository = GroupRepository(
        db=database_engine,
        config_provider=service_mock_args["config_provider"],
        valkey_stat_client=service_mock_args["valkey_stat_client"],
    )

    # Mock the _role_manager with all required methods
    mock_role_manager = MagicMock()
    mock_role_manager.create_system_role = AsyncMock(return_value=None)
    group_repository._role_manager = mock_role_manager
    admin_group_repository = AdminGroupRepository(
        db=database_engine, storage_manager=service_mock_args["storage_manager"]
    )
    group_repositories = GroupRepositories(
        repository=group_repository, admin_repository=admin_group_repository
    )
    group_service = GroupService(
        storage_manager=service_mock_args["storage_manager"],
        config_provider=service_mock_args["config_provider"],
        valkey_stat_client=service_mock_args["valkey_stat_client"],
        group_repositories=group_repositories,
    )
    return GroupProcessors(group_service, [mock_action_monitor])


@asynccontextmanager
async def create_group(
    database_engine: ExtendedAsyncSAEngine,
    *,
    domain_name: str,
    name: str,
    type: ProjectType = ProjectType.GENERAL,
    resource_policy_name: str = "default",
    description: str = "Test group",
    is_active: bool = True,
    total_resource_slots: ResourceSlot = ResourceSlot.from_user_input({}, None),
    allowed_vfolder_hosts: VFolderHostPermissionMap = VFolderHostPermissionMap({}),
) -> AsyncGenerator[Any, Any]:
    # NOTICE: To use 'default' resource policy, you must use `database_fixture` concurrently in test function
    async with database_engine.begin_session() as session:
        group_id = uuid.uuid4()
        group_data = {
            "id": group_id,
            "name": name,
            "description": description,
            "is_active": is_active,
            "domain_name": domain_name,
            "total_resource_slots": total_resource_slots,
            "allowed_vfolder_hosts": allowed_vfolder_hosts,
            "resource_policy": resource_policy_name,
            "type": type,
        }
        await session.execute(sa.insert(GroupRow).values(group_data))

    try:
        yield group_id
    finally:
        async with database_engine.begin_session() as session:
            await session.execute(sa.delete(GroupRow).where(GroupRow.id == group_id))


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "test_scenario",
    [
        ScenarioBase.success(
            "When trigger create group action with valid data, group creation should be successful",
            CreateGroupAction(
                creator=Creator(
                    spec=GroupCreatorSpec(
                        name="test_create_group",
                        type=ProjectType.GENERAL,
                        description="test group description",
                        resource_policy="default",
                        total_resource_slots=ResourceSlot.from_user_input({}, None),
                        domain_name="default",
                        is_active=True,
                    )
                ),
            ),
            CreateGroupActionResult(
                data=GroupData(
                    id=uuid.uuid4(),
                    name="test_create_group",
                    description="test group description",
                    is_active=True,
                    created_at=datetime.now(),
                    modified_at=datetime.now(),
                    integration_id=None,
                    domain_name="default",
                    total_resource_slots=ResourceSlot.from_user_input({}, None),
                    allowed_vfolder_hosts=VFolderHostPermissionMap({}),
                    dotfiles=b"\x90",
                    resource_policy="default",
                    type=ProjectType.GENERAL,
                    container_registry={},
                ),
            ),
        ),
        ScenarioBase.failure(
            "With duplicated name, group creation should be failed",
            CreateGroupAction(
                creator=Creator(
                    spec=GroupCreatorSpec(
                        name="default",
                        type=ProjectType.GENERAL,
                        description="duplicate group",
                        resource_policy="default",
                        total_resource_slots=ResourceSlot.from_user_input({}, None),
                        domain_name="default",
                    )
                ),
            ),
            InvalidAPIParameters,
        ),
        ScenarioBase.failure(
            "When trigger create group action with invalid resource policy, group creation should be failed",
            CreateGroupAction(
                creator=Creator(
                    spec=GroupCreatorSpec(
                        name="test_create_group_without_resource_policy",
                        type=ProjectType.GENERAL,
                        description="test group description",
                        resource_policy="",
                        total_resource_slots=ResourceSlot.from_user_input({}, None),
                        domain_name="default",
                    )
                )
            ),
            InvalidAPIParameters,
        ),
    ],
)
async def test_create_group(
    processors: GroupProcessors,
    test_scenario: ScenarioBase[CreateGroupAction, CreateGroupActionResult],
) -> None:
    await test_scenario.test(processors.create_group.wait_for_complete)


@pytest.mark.asyncio
async def test_modify_group(
    processors: GroupProcessors,
    database_engine: ExtendedAsyncSAEngine,
) -> None:
    async with create_group(
        database_engine=database_engine, domain_name="default", name="test_modfiy_group"
    ) as group_id:
        action = ModifyGroupAction(
            group_id=group_id,
            modifier=GroupModifier(
                name=OptionalState.update("modified_name"),
                description=TriState.update("modified description"),
                is_active=OptionalState.update(False),
            ),
        )
        result: ModifyGroupActionResult = await processors.modify_group.wait_for_complete(action)
        group_data: Optional[GroupData] = result.data

        assert group_data is not None
        assert group_data.name == "modified_name"
        assert group_data.description == "modified description"
        assert group_data.is_active is False


async def test_modify_group_with_invalid_group_id(
    processors: GroupProcessors,
) -> None:
    action = ModifyGroupAction(
        group_id=uuid.UUID("00000000-0000-0000-0000-000000000000"),
        modifier=GroupModifier(
            name=OptionalState.update("modified_name"),
            description=TriState.update("modified description"),
            is_active=OptionalState.update(False),
        ),
    )
    with pytest.raises(ProjectNotFound):
        await processors.modify_group.wait_for_complete(action)


@pytest.mark.asyncio
async def test_delete_group(
    processors: GroupProcessors,
    database_engine: ExtendedAsyncSAEngine,
) -> None:
    async with create_group(
        database_engine=database_engine, domain_name="default", name="test_delete_group"
    ) as group_id:
        action = DeleteGroupAction(group_id=group_id)
        result: DeleteGroupActionResult = await processors.delete_group.wait_for_complete(action)
        assert result.group_id == group_id


@pytest.mark.asyncio
async def test_delete_group_action_effect_in_db(
    processors: GroupProcessors,
    database_engine: ExtendedAsyncSAEngine,
) -> None:
    async with create_group(
        database_engine=database_engine, domain_name="default", name="test_delete_group_in_db"
    ) as group_id:
        action = DeleteGroupAction(group_id=group_id)
        await processors.delete_group.wait_for_complete(action)
        async with database_engine.begin_session() as session:
            group = await session.scalar(sa.select(GroupRow).where(GroupRow.id == group_id))

            assert group is not None
            assert group.is_active is False
            assert group.integration_id is None


@pytest.mark.asyncio
async def test_purge_group(
    processors: GroupProcessors,
    database_engine: ExtendedAsyncSAEngine,
) -> None:
    async with create_group(
        database_engine=database_engine, domain_name="default", name="test_purge_group"
    ) as group_id:
        await processors.delete_group.wait_for_complete(DeleteGroupAction(group_id))

        # No exception should be raised
        await processors.purge_group.wait_for_complete(PurgeGroupAction(group_id))


@pytest.mark.asyncio
async def test_purge_group_action_effect_in_db(
    processors: GroupProcessors,
    database_engine: ExtendedAsyncSAEngine,
) -> None:
    async with create_group(
        database_engine=database_engine, domain_name="default", name="test_purge_group_in_db"
    ) as group_id:
        await processors.delete_group.wait_for_complete(DeleteGroupAction(group_id))
        await processors.purge_group.wait_for_complete(PurgeGroupAction(group_id))

        async with database_engine.begin_session() as session:
            group = await session.scalar(sa.select(GroupRow).where(GroupRow.id == group_id))
            assert group is None
