import asyncio

import pytest
import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError

from ai.backend.manager.data.resource.types import ProjectResourcePolicyData
from ai.backend.manager.errors.common import ObjectNotFound
from ai.backend.manager.models.resource_policy import ProjectResourcePolicyRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.project_resource_policy.repository import (
    ProjectResourcePolicyRepository,
)


@pytest.fixture
def project_resource_policy_repository(
    database_engine: ExtendedAsyncSAEngine,
) -> ProjectResourcePolicyRepository:
    return ProjectResourcePolicyRepository(db=database_engine)


async def test_create_project_resource_policy(
    project_resource_policy_repository: ProjectResourcePolicyRepository,
    database_engine: ExtendedAsyncSAEngine,
) -> None:
    # Arrange
    policy_data = {
        "name": "test-create-policy",
        "max_vfolder_count": 10,
        "max_quota_scope_size": 1073741824,  # 1GB
        "max_network_count": 5,
    }

    # Act
    result = await project_resource_policy_repository.create(policy_data)

    # Assert
    assert isinstance(result, ProjectResourcePolicyData)
    assert result.name == "test-create-policy"
    assert result.max_vfolder_count == 10
    assert result.max_quota_scope_size == 1073741824
    assert result.max_network_count == 5

    # Verify in database
    async with database_engine.begin_session() as session:
        query = sa.select(ProjectResourcePolicyRow).where(
            ProjectResourcePolicyRow.name == "test-create-policy"
        )
        db_row = (await session.execute(query)).scalar_one()
        assert db_row is not None
        assert db_row.name == "test-create-policy"

    # Cleanup
    async with database_engine.begin_session() as session:
        await session.execute(
            sa.delete(ProjectResourcePolicyRow).where(
                ProjectResourcePolicyRow.name == "test-create-policy"
            )
        )


async def test_create_duplicate_policy_fails(
    project_resource_policy_repository: ProjectResourcePolicyRepository,
    database_engine: ExtendedAsyncSAEngine,
) -> None:
    # Create first policy
    policy_data = {
        "name": "duplicate-test-policy",
        "max_vfolder_count": 10,
        "max_quota_scope_size": 1073741824,
        "max_network_count": 5,
    }
    await project_resource_policy_repository.create(policy_data)

    # Try to create duplicate
    with pytest.raises(IntegrityError):
        await project_resource_policy_repository.create(policy_data)

    # Cleanup
    async with database_engine.begin_session() as session:
        await session.execute(
            sa.delete(ProjectResourcePolicyRow).where(
                ProjectResourcePolicyRow.name == "duplicate-test-policy"
            )
        )


async def test_get_by_name(
    project_resource_policy_repository: ProjectResourcePolicyRepository,
    database_engine: ExtendedAsyncSAEngine,
) -> None:
    # Setup: Create a policy directly in database
    policy_name = "test-get-policy"
    async with database_engine.begin_session() as session:
        await session.execute(
            sa.insert(ProjectResourcePolicyRow).values(
                name=policy_name,
                max_vfolder_count=20,
                max_quota_scope_size=2147483648,  # 2GB
                max_network_count=10,
            )
        )

    # Act
    result = await project_resource_policy_repository.get_by_name(policy_name)

    # Assert
    assert isinstance(result, ProjectResourcePolicyData)
    assert result.name == policy_name
    assert result.max_vfolder_count == 20
    assert result.max_quota_scope_size == 2147483648
    assert result.max_network_count == 10

    # Cleanup
    async with database_engine.begin_session() as session:
        await session.execute(
            sa.delete(ProjectResourcePolicyRow).where(ProjectResourcePolicyRow.name == policy_name)
        )


async def test_get_by_name_not_found(
    project_resource_policy_repository: ProjectResourcePolicyRepository,
) -> None:
    with pytest.raises(ObjectNotFound) as exc_info:
        await project_resource_policy_repository.get_by_name("non-existent-policy")

    assert "Project resource policy with name non-existent-policy not found" in str(exc_info.value)


async def test_update_all_fields(
    project_resource_policy_repository: ProjectResourcePolicyRepository,
    database_engine: ExtendedAsyncSAEngine,
) -> None:
    # Setup: Create a policy
    policy_name = "test-update-all-policy"
    async with database_engine.begin_session() as session:
        await session.execute(
            sa.insert(ProjectResourcePolicyRow).values(
                name=policy_name,
                max_vfolder_count=10,
                max_quota_scope_size=1073741824,
                max_network_count=5,
            )
        )

    # Act: Update all fields
    update_fields = {
        "max_vfolder_count": 30,
        "max_quota_scope_size": 3221225472,  # 3GB
        "max_network_count": 15,
    }
    result = await project_resource_policy_repository.update(policy_name, update_fields)

    # Assert
    assert result.name == policy_name
    assert result.max_vfolder_count == 30
    assert result.max_quota_scope_size == 3221225472
    assert result.max_network_count == 15

    # Verify in database
    async with database_engine.begin_session() as session:
        query = sa.select(ProjectResourcePolicyRow).where(
            ProjectResourcePolicyRow.name == policy_name
        )
        db_row = (await session.execute(query)).scalar_one()
        assert db_row.max_vfolder_count == 30
        assert db_row.max_quota_scope_size == 3221225472
        assert db_row.max_network_count == 15

    # Cleanup
    async with database_engine.begin_session() as session:
        await session.execute(
            sa.delete(ProjectResourcePolicyRow).where(ProjectResourcePolicyRow.name == policy_name)
        )


async def test_update_partial_fields(
    project_resource_policy_repository: ProjectResourcePolicyRepository,
    database_engine: ExtendedAsyncSAEngine,
) -> None:
    # Setup: Create a policy
    policy_name = "test-update-partial-policy"
    async with database_engine.begin_session() as session:
        await session.execute(
            sa.insert(ProjectResourcePolicyRow).values(
                name=policy_name,
                max_vfolder_count=10,
                max_quota_scope_size=1073741824,
                max_network_count=5,
            )
        )

    # Act: Update only one field
    update_fields = {"max_vfolder_count": 25}
    result = await project_resource_policy_repository.update(policy_name, update_fields)

    # Assert
    assert result.name == policy_name
    assert result.max_vfolder_count == 25
    assert result.max_quota_scope_size == 1073741824  # Unchanged
    assert result.max_network_count == 5  # Unchanged

    # Cleanup
    async with database_engine.begin_session() as session:
        await session.execute(
            sa.delete(ProjectResourcePolicyRow).where(ProjectResourcePolicyRow.name == policy_name)
        )


async def test_update_not_found(
    project_resource_policy_repository: ProjectResourcePolicyRepository,
) -> None:
    update_fields = {"max_vfolder_count": 50}

    with pytest.raises(ObjectNotFound) as exc_info:
        await project_resource_policy_repository.update("non-existent-policy", update_fields)

    assert "Project resource policy with name non-existent-policy not found" in str(exc_info.value)


async def test_delete(
    project_resource_policy_repository: ProjectResourcePolicyRepository,
    database_engine: ExtendedAsyncSAEngine,
) -> None:
    # Setup: Create a policy
    policy_name = "test-delete-policy"
    async with database_engine.begin_session() as session:
        await session.execute(
            sa.insert(ProjectResourcePolicyRow).values(
                name=policy_name,
                max_vfolder_count=10,
                max_quota_scope_size=1073741824,
                max_network_count=5,
            )
        )

    # Act
    result = await project_resource_policy_repository.delete(policy_name)

    # Assert: Returns deleted data
    assert result.name == policy_name
    assert result.max_vfolder_count == 10
    assert result.max_quota_scope_size == 1073741824
    assert result.max_network_count == 5

    # Verify deletion in database
    async with database_engine.begin_session() as session:
        query = sa.select(ProjectResourcePolicyRow).where(
            ProjectResourcePolicyRow.name == policy_name
        )
        db_row = (await session.execute(query)).scalar_one_or_none()
        assert db_row is None


async def test_delete_not_found(
    project_resource_policy_repository: ProjectResourcePolicyRepository,
) -> None:
    with pytest.raises(ObjectNotFound) as exc_info:
        await project_resource_policy_repository.delete("non-existent-policy")

    assert "Project resource policy with name non-existent-policy not found" in str(exc_info.value)


async def test_repository_with_zero_values(
    project_resource_policy_repository: ProjectResourcePolicyRepository,
    database_engine: ExtendedAsyncSAEngine,
) -> None:
    # Test creating policy with zero values (edge case)
    policy_data = {
        "name": "test-zero-values-policy",
        "max_vfolder_count": 0,
        "max_quota_scope_size": 0,
        "max_network_count": 0,
    }

    result = await project_resource_policy_repository.create(policy_data)

    # Assert: Zero values should be stored correctly
    assert result.name == "test-zero-values-policy"
    assert result.max_vfolder_count == 0
    assert result.max_quota_scope_size == 0
    assert result.max_network_count == 0

    # Cleanup
    async with database_engine.begin_session() as session:
        await session.execute(
            sa.delete(ProjectResourcePolicyRow).where(
                ProjectResourcePolicyRow.name == "test-zero-values-policy"
            )
        )


async def test_update_with_empty_fields(
    project_resource_policy_repository: ProjectResourcePolicyRepository,
    database_engine: ExtendedAsyncSAEngine,
) -> None:
    # Setup: Create a policy
    policy_name = "test-empty-update-policy"
    async with database_engine.begin_session() as session:
        await session.execute(
            sa.insert(ProjectResourcePolicyRow).values(
                name=policy_name,
                max_vfolder_count=10,
                max_quota_scope_size=1073741824,
                max_network_count=5,
            )
        )

    # Act: Update with empty dict (should not change anything)
    result = await project_resource_policy_repository.update(policy_name, {})

    # Assert: Nothing should change
    assert result.name == policy_name
    assert result.max_vfolder_count == 10
    assert result.max_quota_scope_size == 1073741824
    assert result.max_network_count == 5

    # Cleanup
    async with database_engine.begin_session() as session:
        await session.execute(
            sa.delete(ProjectResourcePolicyRow).where(ProjectResourcePolicyRow.name == policy_name)
        )


async def test_concurrent_operations(
    project_resource_policy_repository: ProjectResourcePolicyRepository,
    database_engine: ExtendedAsyncSAEngine,
) -> None:
    """Test that repository handles concurrent operations correctly"""

    policy_name = "test-concurrent-policy"

    # Create initial policy
    await project_resource_policy_repository.create({
        "name": policy_name,
        "max_vfolder_count": 10,
        "max_quota_scope_size": 1073741824,
        "max_network_count": 5,
    })

    # Define concurrent update operations
    async def update_vfolder_count():
        return await project_resource_policy_repository.update(
            policy_name, {"max_vfolder_count": 20}
        )

    async def update_quota_size():
        return await project_resource_policy_repository.update(
            policy_name, {"max_quota_scope_size": 2147483648}
        )

    # Run updates concurrently
    results = await asyncio.gather(update_vfolder_count(), update_quota_size())

    # Both operations should succeed, last one wins for each field
    for result in results:
        assert result.name == policy_name

    # Verify final state
    final_policy = await project_resource_policy_repository.get_by_name(policy_name)
    assert final_policy.max_vfolder_count == 20
    assert final_policy.max_quota_scope_size == 2147483648

    # Cleanup
    async with database_engine.begin_session() as session:
        await session.execute(
            sa.delete(ProjectResourcePolicyRow).where(ProjectResourcePolicyRow.name == policy_name)
        )
