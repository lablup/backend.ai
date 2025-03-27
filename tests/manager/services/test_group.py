import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, AsyncGenerator, Optional
from unittest.mock import MagicMock

import pytest
import sqlalchemy as sa

from ai.backend.common.types import ResourceSlot, VFolderHostPermissionMap
from ai.backend.manager.models.group import GroupRow, ProjectType
from ai.backend.manager.models.storage import StorageSessionManager
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.services.groups.actions.create_group import (
    CreateGroupAction,
    CreateGroupActionResult,
)
from ai.backend.manager.services.groups.actions.delete_group import (
    DeleteGroupAction,
    DeleteGroupActionResult,
)
from ai.backend.manager.services.groups.actions.modify_group import (
    ModifyGroupAction,
    ModifyGroupActionResult,
)
from ai.backend.manager.services.groups.actions.purge_group import (
    PurgeGroupAction,
    PurgeGroupActionResult,
)
from ai.backend.manager.services.groups.processors import GroupProcessors
from ai.backend.manager.services.groups.service import GroupService
from ai.backend.manager.services.groups.types import GroupData

from .test_utils import TestScenario


@pytest.fixture
def mock_storage_manager():
    mock_storage_manager = MagicMock(spec=StorageSessionManager)
    return mock_storage_manager


@pytest.fixture
def processors(database_fixture, database_engine, mock_storage_manager) -> GroupProcessors:
    group_service = GroupService(db=database_engine, storage_manager=mock_storage_manager)
    return GroupProcessors(group_service)


@asynccontextmanager
async def create_group(
    database_engine: ExtendedAsyncSAEngine,
    *,
    domain_name: str,
    name: str,
    type: ProjectType = ProjectType.GENERAL,
    resource_policy_name: str = "default",
) -> AsyncGenerator[Any, Any]:
    # NOTICE: To use 'default' resource policy, you must use `database_fixture` concurrently in test function
    async with database_engine.begin_session() as session:
        group_id = uuid.uuid4()
        group_data = {
            "id": group_id,
            "name": name,
            "description": "Test group",
            "is_active": True,
            "domain_name": domain_name,
            "total_resource_slots": {},
            "allowed_vfolder_hosts": {},
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
            "Create a group",
            CreateGroupAction(
                name="test_create_group",
                type=ProjectType.GENERAL,
                description="test group description",
                domain_name="default",
            ),
            CreateGroupActionResult(
                data=GroupData(
                    id=uuid.uuid4(),
                    name="test_create_group",
                    description="test group description",
                    is_active=True,
                    created_at=datetime.now(),
                    modified_at=datetime.now(),
                    integration_id="",
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
            "Create a group with duplicated name",
            CreateGroupAction(
                name="default",
                type=ProjectType.GENERAL,
                description="duplicate group name",
                domain_name="default",
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
            name="modified_name",
            description="modified description",
            is_active=False,
        )
        result: ModifyGroupActionResult = await processors.modify_group.wait_for_complete(action)
        group_data: Optional[GroupData] = result.data

        assert group_data is not None
        assert group_data.name == "modified_name"
        assert group_data.description == "modified description"
        assert group_data.is_active == False  # noqa: E712


async def test_modify_group_with_invalid_group_id(
    processors: GroupProcessors,
) -> None:
    action = ModifyGroupAction(
        group_id=uuid.UUID("00000000-0000-0000-0000-000000000000"),
        name="modified_name",
        description="modified description",
        is_active=False,
    )
    result: ModifyGroupActionResult = await processors.modify_group.wait_for_complete(action)
    assert result.data is None
    assert result.success == False  # noqa


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
        assert result.success == True  # noqa: E712


@pytest.mark.asyncio
async def test_delete_group_in_db(
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
            assert group.is_active == False  # noqa: E712
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
        assert result.success == True  # noqa: E712


@pytest.mark.asyncio
async def test_purge_group_in_db(
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
