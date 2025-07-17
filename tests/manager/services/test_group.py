import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, AsyncGenerator, Optional
from unittest.mock import MagicMock

import pytest
import sqlalchemy as sa

from ai.backend.common.types import RedisConnectionInfo, ResourceSlot, VFolderHostPermissionMap
from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.models.group import GroupRow, ProjectType
from ai.backend.manager.models.storage import StorageSessionManager
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.group.admin_repository import AdminGroupRepository
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
    PurgeGroupActionResult,
)
from ai.backend.manager.services.group.processors import GroupProcessors
from ai.backend.manager.services.group.service import GroupService
from ai.backend.manager.services.group.types import GroupCreator, GroupData, GroupModifier
from ai.backend.manager.types import OptionalState, TriState

from .test_utils import TestScenario


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
        TestScenario.success(
            "When trigger create group action with valid data, group creation should be successful",
            CreateGroupAction(
                input=GroupCreator(
                    name="test_create_group",
                    type=ProjectType.GENERAL,
                    description="test group description",
                    resource_policy="default",
                    total_resource_slots=ResourceSlot.from_user_input({}, None),
                    domain_name="default",
                    is_active=True,
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
                success=True,
            ),
        ),
        # TODO: If business logic is implemented to raise exception instead of returning None
        # we need to update TestScenario.failure
        TestScenario.success(
            "With duplicated name, group creation should be failed",
            CreateGroupAction(
                input=GroupCreator(
                    name="default",
                    type=ProjectType.GENERAL,
                    description="duplicate group",
                    resource_policy="default",
                    total_resource_slots=ResourceSlot.from_user_input({}, None),
                    domain_name="default",
                ),
            ),
            CreateGroupActionResult(
                data=None,
                success=False,
            ),
        ),
        TestScenario.success(
            "When trigger create group action with invalid resource policy, group creation should be failed",
            CreateGroupAction(
                input=GroupCreator(
                    name="test_create_group_without_resource_policy",
                    type=ProjectType.GENERAL,
                    description="test group description",
                    resource_policy="",
                    total_resource_slots=ResourceSlot.from_user_input({}, None),
                    domain_name="default",
                )
            ),
            CreateGroupActionResult(
                data=None,
                success=False,
            ),
        ),
    ],
)
async def test_create_group(
    processors: GroupProcessors,
    test_scenario: TestScenario[CreateGroupAction, CreateGroupActionResult],
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


@pytest.mark.asyncio
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
    result: ModifyGroupActionResult = await processors.modify_group.wait_for_complete(action)
    assert result.data is None
    assert result.success is False


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
        assert result.data is None
        assert result.success is True


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

        result: PurgeGroupActionResult = await processors.purge_group.wait_for_complete(
            PurgeGroupAction(group_id)
        )
        assert result.data is None
        assert result.success is True


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


# Additional comprehensive tests for GroupService actions
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "action",
    [
        CreateGroupAction(
            input=GroupCreator(
                name="minimal_group",
                type=ProjectType.GENERAL,
                description="",
                resource_policy="default",
                total_resource_slots=ResourceSlot.from_user_input({}, None),
                domain_name="default",
                is_active=True,
            ),
        ),
        CreateGroupAction(
            input=GroupCreator(
                name="full_group",
                type=ProjectType.GENERAL,
                description="Complete group with all fields",
                resource_policy="default",
                total_resource_slots=ResourceSlot.from_user_input({"cpu": "4", "mem": "8g"}, None),
                domain_name="default",
                is_active=True,
            ),
        ),
        CreateGroupAction(
            input=GroupCreator(
                name="inactive_group",
                type=ProjectType.GENERAL,
                description="Inactive group",
                resource_policy="default",
                total_resource_slots=ResourceSlot.from_user_input({}, None),
                domain_name="default",
                is_active=False,
            ),
        ),
        CreateGroupAction(
            input=GroupCreator(
                name="model_group",
                type=ProjectType.MODEL_STORE,
                description="Model store group",
                resource_policy="default",
                total_resource_slots=ResourceSlot.from_user_input({}, None),
                domain_name="default",
                is_active=True,
            ),
        ),
    ],
)
async def test_create_group_comprehensive(
    processors: GroupProcessors,
    action: CreateGroupAction,
) -> None:
    """Comprehensive test for CreateGroupAction with various scenarios"""
    result = await processors.create_group.wait_for_complete(action)
    assert result.success is True
    assert result.data is not None
    assert result.data.name == action.input.name
    assert result.data.type == action.input.type
    assert result.data.description == action.input.description
    assert result.data.is_active == action.input.is_active


@pytest.mark.asyncio
async def test_create_group_error_handling(
    processors: GroupProcessors,
) -> None:
    """Test CreateGroupAction error handling"""
    # Test with empty resource policy
    action = CreateGroupAction(
        input=GroupCreator(
            name="test_empty_policy",
            type=ProjectType.GENERAL,
            description="test",
            resource_policy="",
            total_resource_slots=ResourceSlot.from_user_input({}, None),
            domain_name="default",
            is_active=True,
        ),
    )
    result = await processors.create_group.wait_for_complete(action)
    assert result.success is False
    assert result.data is None


@pytest.mark.asyncio
async def test_create_group_duplicate_name(
    processors: GroupProcessors,
) -> None:
    """Test CreateGroupAction with duplicate name"""
    # Test with duplicate name (default group already exists)
    action = CreateGroupAction(
        input=GroupCreator(
            name="default",
            type=ProjectType.GENERAL,
            description="duplicate group",
            resource_policy="default",
            total_resource_slots=ResourceSlot.from_user_input({}, None),
            domain_name="default",
        ),
    )
    result = await processors.create_group.wait_for_complete(action)
    assert result.success is False
    assert result.data is None


# Additional ModifyGroupAction tests
@pytest.mark.asyncio
async def test_modify_group_single_field_name(
    processors: GroupProcessors,
    database_engine: ExtendedAsyncSAEngine,
) -> None:
    """Test ModifyGroupAction with only name change"""
    async with create_group(
        database_engine=database_engine, domain_name="default", name="test_single_name"
    ) as group_id:
        action = ModifyGroupAction(
            group_id=group_id,
            modifier=GroupModifier(
                name=OptionalState.update("single_name_modified"),
            ),
        )
        result = await processors.modify_group.wait_for_complete(action)
        assert result.success is True
        assert result.data is not None
        assert result.data.name == "single_name_modified"


@pytest.mark.asyncio
async def test_modify_group_single_field_description(
    processors: GroupProcessors,
    database_engine: ExtendedAsyncSAEngine,
) -> None:
    """Test ModifyGroupAction with only description change"""
    async with create_group(
        database_engine=database_engine, domain_name="default", name="test_single_desc"
    ) as group_id:
        action = ModifyGroupAction(
            group_id=group_id,
            modifier=GroupModifier(
                description=TriState.update("single description modified"),
            ),
        )
        result = await processors.modify_group.wait_for_complete(action)
        assert result.success is True
        assert result.data is not None
        assert result.data.description == "single description modified"


@pytest.mark.asyncio
async def test_modify_group_single_field_is_active(
    processors: GroupProcessors,
    database_engine: ExtendedAsyncSAEngine,
) -> None:
    """Test ModifyGroupAction with only is_active change"""
    async with create_group(
        database_engine=database_engine, domain_name="default", name="test_single_active"
    ) as group_id:
        action = ModifyGroupAction(
            group_id=group_id,
            modifier=GroupModifier(
                is_active=OptionalState.update(False),
            ),
        )
        result = await processors.modify_group.wait_for_complete(action)
        assert result.success is True
        assert result.data is not None
        assert result.data.is_active is False


@pytest.mark.asyncio
async def test_modify_group_multiple_fields(
    processors: GroupProcessors,
    database_engine: ExtendedAsyncSAEngine,
) -> None:
    """Test ModifyGroupAction with multiple field changes"""
    async with create_group(
        database_engine=database_engine, domain_name="default", name="test_multiple_fields"
    ) as group_id:
        action = ModifyGroupAction(
            group_id=group_id,
            modifier=GroupModifier(
                name=OptionalState.update("multiple_fields_name"),
                description=TriState.update("multiple fields description"),
                is_active=OptionalState.update(False),
            ),
        )
        result = await processors.modify_group.wait_for_complete(action)
        assert result.success is True
        assert result.data is not None
        assert result.data.name == "multiple_fields_name"
        assert result.data.description == "multiple fields description"
        assert result.data.is_active is False


@pytest.mark.asyncio
async def test_modify_group_description_null_handling(
    processors: GroupProcessors,
    database_engine: ExtendedAsyncSAEngine,
) -> None:
    """Test ModifyGroupAction with description set to null"""
    async with create_group(
        database_engine=database_engine, domain_name="default", name="test_null_description"
    ) as group_id:
        # Set description to null
        action = ModifyGroupAction(
            group_id=group_id,
            modifier=GroupModifier(
                description=TriState.update(None),
            ),
        )
        result = await processors.modify_group.wait_for_complete(action)
        assert result.success is True
        assert result.data is not None
        assert result.data.description is None


# Comprehensive DeleteGroupAction tests
@pytest.mark.asyncio
async def test_delete_group_success(
    processors: GroupProcessors,
    database_engine: ExtendedAsyncSAEngine,
) -> None:
    """Test successful DeleteGroupAction"""
    async with create_group(
        database_engine=database_engine, domain_name="default", name="test_delete_success"
    ) as group_id:
        action = DeleteGroupAction(group_id=group_id)
        result = await processors.delete_group.wait_for_complete(action)
        assert result.success is True
        assert result.data is None

        # Verify group is marked as inactive in database
        async with database_engine.begin_session() as session:
            group = await session.scalar(sa.select(GroupRow).where(GroupRow.id == group_id))
            assert group is not None
            assert group.is_active is False
            assert group.integration_id is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "group_type",
    [
        ProjectType.GENERAL,
        ProjectType.MODEL_STORE,
    ],
)
async def test_delete_group_different_types(
    processors: GroupProcessors,
    database_engine: ExtendedAsyncSAEngine,
    group_type: ProjectType,
) -> None:
    """Test DeleteGroupAction with different project types"""
    async with create_group(
        database_engine=database_engine,
        domain_name="default",
        name=f"test_delete_{group_type.name.lower()}",
        type=group_type,
    ) as group_id:
        action = DeleteGroupAction(group_id=group_id)
        result = await processors.delete_group.wait_for_complete(action)
        assert result.success is True
        assert result.data is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "invalid_group_id",
    [
        uuid.UUID("00000000-0000-0000-0000-000000000001"),
        uuid.UUID("22222222-2222-2222-2222-222222222222"),
        uuid.UUID("eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee"),
    ],
)
async def test_delete_group_nonexistent(
    processors: GroupProcessors,
    invalid_group_id: uuid.UUID,
) -> None:
    """Test DeleteGroupAction with nonexistent group IDs"""
    action = DeleteGroupAction(group_id=invalid_group_id)
    result = await processors.delete_group.wait_for_complete(action)
    assert result.success is False
    assert result.data is None


@pytest.mark.asyncio
async def test_delete_group_already_inactive(
    processors: GroupProcessors,
    database_engine: ExtendedAsyncSAEngine,
) -> None:
    """Test DeleteGroupAction on already inactive group"""
    async with create_group(
        database_engine=database_engine,
        domain_name="default",
        name="test_already_inactive",
        is_active=False,
    ) as group_id:
        action = DeleteGroupAction(group_id=group_id)
        result = await processors.delete_group.wait_for_complete(action)
        assert result.success is True
        assert result.data is None


@pytest.mark.asyncio
async def test_delete_group_multiple_times(
    processors: GroupProcessors,
    database_engine: ExtendedAsyncSAEngine,
) -> None:
    """Test DeleteGroupAction called multiple times on same group"""
    async with create_group(
        database_engine=database_engine, domain_name="default", name="test_multiple_deletes"
    ) as group_id:
        # First deletion
        action = DeleteGroupAction(group_id=group_id)
        result1 = await processors.delete_group.wait_for_complete(action)
        assert result1.success is True
        assert result1.data is None

        # Second deletion (should still work as it's a soft delete)
        result2 = await processors.delete_group.wait_for_complete(action)
        assert result2.success is True
        assert result2.data is None


# Comprehensive PurgeGroupAction tests
@pytest.mark.asyncio
async def test_purge_group_success(
    processors: GroupProcessors,
    database_engine: ExtendedAsyncSAEngine,
) -> None:
    """Test successful PurgeGroupAction"""
    async with create_group(
        database_engine=database_engine, domain_name="default", name="test_purge_success"
    ) as group_id:
        # First mark group as inactive
        delete_action = DeleteGroupAction(group_id=group_id)
        await processors.delete_group.wait_for_complete(delete_action)

        # Then purge the group
        purge_action = PurgeGroupAction(group_id=group_id)
        result = await processors.purge_group.wait_for_complete(purge_action)
        assert result.success is True
        assert result.data is None

        # Verify group is completely removed from database
        async with database_engine.begin_session() as session:
            group = await session.scalar(sa.select(GroupRow).where(GroupRow.id == group_id))
            assert group is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "group_type",
    [
        ProjectType.GENERAL,
        ProjectType.MODEL_STORE,
    ],
)
async def test_purge_group_different_types(
    processors: GroupProcessors,
    database_engine: ExtendedAsyncSAEngine,
    group_type: ProjectType,
) -> None:
    """Test PurgeGroupAction with different project types"""
    async with create_group(
        database_engine=database_engine,
        domain_name="default",
        name=f"test_purge_{group_type.name.lower()}",
        type=group_type,
    ) as group_id:
        # First mark group as inactive
        delete_action = DeleteGroupAction(group_id=group_id)
        await processors.delete_group.wait_for_complete(delete_action)

        # Then purge the group
        purge_action = PurgeGroupAction(group_id=group_id)
        result = await processors.purge_group.wait_for_complete(purge_action)
        assert result.success is True
        assert result.data is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "invalid_group_id",
    [
        uuid.UUID("00000000-0000-0000-0000-000000000002"),
        uuid.UUID("33333333-3333-3333-3333-333333333333"),
        uuid.UUID("dddddddd-dddd-dddd-dddd-dddddddddddd"),
    ],
)
async def test_purge_group_nonexistent(
    processors: GroupProcessors,
    invalid_group_id: uuid.UUID,
) -> None:
    """Test PurgeGroupAction with nonexistent group IDs"""
    action = PurgeGroupAction(group_id=invalid_group_id)
    result = await processors.purge_group.wait_for_complete(action)
    assert result.success is False
    assert result.data is None


@pytest.mark.asyncio
async def test_purge_group_without_delete_first(
    processors: GroupProcessors,
    database_engine: ExtendedAsyncSAEngine,
) -> None:
    """Test PurgeGroupAction without deleting first (should still work)"""
    async with create_group(
        database_engine=database_engine, domain_name="default", name="test_purge_without_delete"
    ) as group_id:
        # Purge without deleting first
        purge_action = PurgeGroupAction(group_id=group_id)
        result = await processors.purge_group.wait_for_complete(purge_action)
        assert result.success is True
        assert result.data is None

        # Verify group is completely removed from database
        async with database_engine.begin_session() as session:
            group = await session.scalar(sa.select(GroupRow).where(GroupRow.id == group_id))
            assert group is None


@pytest.mark.asyncio
async def test_purge_group_multiple_times(
    processors: GroupProcessors,
    database_engine: ExtendedAsyncSAEngine,
) -> None:
    """Test PurgeGroupAction called multiple times on same group"""
    async with create_group(
        database_engine=database_engine, domain_name="default", name="test_multiple_purges"
    ) as group_id:
        # First purge
        purge_action = PurgeGroupAction(group_id=group_id)
        result1 = await processors.purge_group.wait_for_complete(purge_action)
        assert result1.success is True
        assert result1.data is None

        # Second purge (should fail as group no longer exists)
        result2 = await processors.purge_group.wait_for_complete(purge_action)
        assert result2.success is False
        assert result2.data is None


# Test workflow: create -> modify -> delete -> purge
@pytest.mark.asyncio
async def test_complete_group_lifecycle(
    processors: GroupProcessors,
    database_engine: ExtendedAsyncSAEngine,
) -> None:
    """Test complete group lifecycle: create -> modify -> delete -> purge"""
    async with create_group(
        database_engine=database_engine, domain_name="default", name="test_lifecycle"
    ) as group_id:
        # 1. Modify the group
        modify_action = ModifyGroupAction(
            group_id=group_id,
            modifier=GroupModifier(
                name=OptionalState.update("lifecycle_modified"),
                description=TriState.update("lifecycle test description"),
            ),
        )
        modify_result = await processors.modify_group.wait_for_complete(modify_action)
        assert modify_result.success is True
        assert modify_result.data.name == "lifecycle_modified"

        # 2. Delete the group (soft delete)
        delete_action = DeleteGroupAction(group_id=group_id)
        delete_result = await processors.delete_group.wait_for_complete(delete_action)
        assert delete_result.success is True

        # 3. Purge the group (hard delete)
        purge_action = PurgeGroupAction(group_id=group_id)
        purge_result = await processors.purge_group.wait_for_complete(purge_action)
        assert purge_result.success is True

        # 4. Verify group is completely removed
        async with database_engine.begin_session() as session:
            group = await session.scalar(sa.select(GroupRow).where(GroupRow.id == group_id))
            assert group is None
