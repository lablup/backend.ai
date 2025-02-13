import uuid
from typing import Callable

import pytest
import sqlalchemy as sa

from ai.backend.common.types import (
    QuotaScopeID,
    QuotaScopeType,
    VFolderUsageMode,
)
from ai.backend.manager.api.exceptions import GroupNotFound, UserNotFound
from ai.backend.manager.api.vfolders.repositories import VFolderRepository
from ai.backend.manager.data.vfolder.dto import UserIdentity, VFolderItem, VFolderMetadataToCreate
from ai.backend.manager.models import (
    ProjectType,
    UserRole,
    VFolderOperationStatus,
    VFolderOwnershipType,
    VFolderPermission,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder import (
    VFolderRow,
)

"""
This test file also use fixtures created in `database_fixture` in tests/conftest.py, especially when using 'default' resource policy.
"""


@pytest.mark.parametrize("project_type", [ProjectType.GENERAL, ProjectType.MODEL_STORE])
@pytest.mark.asyncio
async def test_get_group_type(
    database_fixture,
    create_domain: Callable,
    create_group: Callable,
    database_engine: ExtendedAsyncSAEngine,
    project_type,
):
    domain_name = await create_domain(name="test_add_permission")
    group_id = await create_group(
        domain_name=domain_name, name="test_get_group_type", type=project_type
    )
    vfolder_repository = VFolderRepository(db=database_engine)
    group_type = await vfolder_repository.get_group_type(group_id=group_id)
    assert isinstance(group_type, ProjectType)
    assert group_type == project_type


@pytest.mark.asyncio
async def test_get_container_id(
    database_fixture,
    database_engine: ExtendedAsyncSAEngine,
    create_user_with_role: Callable,
    create_domain: Callable,
):
    domain_name = await create_domain(name="test_get_container_id")
    expected_container_id = 1234
    user_id = await create_user_with_role(
        domain_name=domain_name,
        role=UserRole.USER,
        name="test_get_container_id",
        container_uid=expected_container_id,
    )

    repo = VFolderRepository(database_engine)
    actual_container_id = await repo.get_user_container_id(user_id=user_id)
    assert actual_container_id == expected_container_id


@pytest.mark.asyncio
async def test_get_created_vfolder_count(
    database_fixture,
    database_engine: ExtendedAsyncSAEngine,
    create_domain: Callable,
    create_user_with_role: Callable,
    create_vfolder: Callable,
    create_group: Callable,
):
    domain_name = await create_domain(name="test_get_created_vfolder_count")
    user_id = await create_user_with_role(
        domain_name=domain_name, role=UserRole.USER, name="test_get_created_vfolder_count"
    )
    group_id = await create_group(domain_name=domain_name, name="test_get_created_vfolder_count")

    # Create 3 user vfolders and delete 1
    await create_vfolder(
        domain_name=domain_name, user_id=user_id, group_id=None, name="user-vfolder-1"
    )
    await create_vfolder(
        domain_name=domain_name, user_id=user_id, group_id=None, name="user-vfolder-2"
    )
    deleted_vfolder_id = await create_vfolder(
        domain_name=domain_name, user_id=user_id, group_id=None, name="deleted-vfolder"
    )
    async with database_engine.begin() as conn:
        await conn.execute(
            sa.update(VFolderRow)
            .where(VFolderRow.id == deleted_vfolder_id)
            .values(status=VFolderOperationStatus.DELETE_COMPLETE)
        )

    # Create 3 group vfolders
    await create_vfolder(
        domain_name=domain_name, user_id=None, group_id=group_id, name="group-vfolder-1"
    )
    await create_vfolder(
        domain_name=domain_name, user_id=None, group_id=group_id, name="group-vfolder-2"
    )
    await create_vfolder(
        domain_name=domain_name, user_id=None, group_id=group_id, name="group-vfolder-3"
    )

    vfolder_repository = VFolderRepository(db=database_engine)
    user_count = await vfolder_repository.get_created_vfolder_count(
        user_id, VFolderOwnershipType.USER
    )
    assert user_count == 2

    group_count = await vfolder_repository.get_created_vfolder_count(
        group_id, VFolderOwnershipType.GROUP
    )
    assert group_count == 3


@pytest.mark.asyncio
async def test_persist_vfolder_metadata(
    database_fixture,
    database_engine: ExtendedAsyncSAEngine,
    create_domain: Callable,
    create_user_with_role: Callable,
):
    domain_name = await create_domain(name="test_persist_vfolder_metadata")
    user_id = await create_user_with_role(
        domain_name=domain_name,
        role=UserRole.USER,
        name="test_persist_vfolder_metadata",
    )
    quota_scope_id = QuotaScopeID(QuotaScopeType.USER, user_id)
    host = "local"

    vfolder_name = "test_persist_vfolder_metadata"
    metadata = VFolderMetadataToCreate(
        name=vfolder_name,
        domain_name=domain_name,
        quota_scope_id=str(quota_scope_id),
        usage_mode=VFolderUsageMode.GENERAL,
        permission=VFolderPermission.READ_WRITE,
        host=host,
        creator=str(user_id),
        ownership_type=VFolderOwnershipType.USER,
        cloneable=True,
    )
    vfolder_repository = VFolderRepository(db=database_engine)
    vfolder_item: VFolderItem = await vfolder_repository.persist_vfolder_metadata(metadata=metadata)
    assert vfolder_item.name == vfolder_name
    assert vfolder_item.host == host
    assert vfolder_item.ownership_type == VFolderOwnershipType.USER
    assert vfolder_item.quota_scope_id == quota_scope_id
    assert vfolder_item.permission == VFolderPermission.READ_WRITE
    assert vfolder_item.creator == str(user_id)
    assert vfolder_item.cloneable == True  # noqa: E712


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "policy_name,vfolder_count,quota_size",
    [
        ("test-user-policy-1", 10, 100000),
        ("test-user-policy-2", 20, 200000),
        ("test-user-policy-3", 0, -1),
    ],
)
async def test_get_user_vfolder_resource_limit(
    database_engine: ExtendedAsyncSAEngine,
    create_domain: Callable,
    create_user_with_role: Callable,
    create_user_resource_policy: Callable,
    policy_name: str,
    vfolder_count: int,
    quota_size: int,
):
    # Given
    domain_name = await create_domain(name=f"test-domain-{policy_name}")
    policy_name = await create_user_resource_policy(
        name=policy_name,
        max_vfolder_count=vfolder_count,
        max_quota_scope_size=quota_size,
    )
    user_id = await create_user_with_role(
        domain_name=domain_name,
        role=UserRole.USER,
        name=f"test-user-{policy_name}",
        resource_policy_name=policy_name,
    )

    # When
    user_identity = UserIdentity(
        user_uuid=user_id,
        domain_name=domain_name,
        user_role=UserRole.USER,
        user_email="test@example.com",
    )
    vfolder_repository = VFolderRepository(db=database_engine)
    resource_limit = await vfolder_repository.get_user_vfolder_resource_limit(user_identity)

    # Then
    assert resource_limit.max_vfolder_count == vfolder_count
    assert resource_limit.max_quota_scope_size == quota_size


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "policy_name,vfolder_count,quota_size",
    [
        ("test-project-policy-1", 20, 20000),
        ("test-project-policy-2", 50, 50000),
        ("test-project-policy-3", 0, -1),
    ],
)
async def test_get_group_vfolder_resource_limit(
    database_engine: ExtendedAsyncSAEngine,
    create_domain: Callable,
    create_user_with_role: Callable,
    create_group: Callable,
    create_project_resource_policy: Callable,
    create_user_resource_policy: Callable,
    policy_name: str,
    vfolder_count: int,
    quota_size: int,
):
    # Given
    domain_name = await create_domain(name=f"test-domain-{policy_name}")

    # Create user resource policy for the user
    user_policy_name = f"user-{policy_name}"
    await create_user_resource_policy(
        name=user_policy_name,
        max_vfolder_count=10,
        max_quota_scope_size=100000,
    )

    # Create project resource policy for the group
    project_policy_name = await create_project_resource_policy(
        name=policy_name,
        max_vfolder_count=vfolder_count,
        max_quota_scope_size=quota_size,
    )

    # Create user with user resource policy
    user_id = await create_user_with_role(
        domain_name=domain_name,
        role=UserRole.USER,
        name=f"test-user-{policy_name}",
        resource_policy_name=user_policy_name,
    )

    # Create group with project resource policy
    group_id = await create_group(
        domain_name=domain_name,
        name=f"test-group-{policy_name}",
        resource_policy_name=project_policy_name,
    )

    # When
    user_identity = UserIdentity(
        user_uuid=user_id,
        domain_name=domain_name,
        user_role=UserRole.USER,
        user_email="test@example.com",
    )
    vfolder_repository = VFolderRepository(db=database_engine)
    resource_limit = await vfolder_repository.get_group_vfolder_resource_limit(
        user_identity=user_identity,
        group_id=group_id,
    )

    # Then
    assert resource_limit.max_vfolder_count == vfolder_count
    assert resource_limit.max_quota_scope_size == quota_size


@pytest.mark.asyncio
async def test_get_user_vfolder_resource_limit_not_found(
    database_fixture,
    database_engine: ExtendedAsyncSAEngine,
):
    # Given
    non_exist_user_id = uuid.uuid4()
    user_identity = UserIdentity(
        user_uuid=non_exist_user_id,
        domain_name="test-domain",
        user_role=UserRole.USER,
        user_email="test@example.com",
    )

    # When & Then
    vfolder_repository = VFolderRepository(db=database_engine)
    with pytest.raises(UserNotFound):
        await vfolder_repository.get_user_vfolder_resource_limit(user_identity)


@pytest.mark.asyncio
async def test_get_group_vfolder_resource_limit_not_found(
    database_fixture,
    database_engine: ExtendedAsyncSAEngine,
    create_domain: Callable,
    create_user_with_role: Callable,
):
    # Given
    domain_name = await create_domain("test-domain")
    user_id = await create_user_with_role(
        domain_name=domain_name,
        role=UserRole.USER,
        name="test-user",
    )
    non_exist_group_id = uuid.uuid4()

    user_identity = UserIdentity(
        user_uuid=user_id,
        domain_name=domain_name,
        user_role=UserRole.USER,
        user_email="test@example.com",
    )

    # When & Then
    vfolder_repository = VFolderRepository(db=database_engine)
    with pytest.raises(GroupNotFound):
        await vfolder_repository.get_group_vfolder_resource_limit(
            user_identity=user_identity,
            group_id=non_exist_group_id,
        )
