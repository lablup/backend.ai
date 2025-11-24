from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING

import pytest
import sqlalchemy as sa

from ai.backend.common.exception import UserResourcePolicyNotFound
from ai.backend.manager.data.resource.types import UserResourcePolicyData
from ai.backend.manager.models.resource_policy import UserResourcePolicyRow
from ai.backend.manager.repositories.user_resource_policy.repository import (
    UserResourcePolicyRepository,
)

if TYPE_CHECKING:
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


class TestUserResourcePolicyRepository:
    """Test suite for UserResourcePolicyRepository"""

    @pytest.fixture
    async def repository(
        self, database_engine: ExtendedAsyncSAEngine
    ) -> UserResourcePolicyRepository:
        """Repository instance with real database"""
        return UserResourcePolicyRepository(db=database_engine)

    @pytest.fixture
    async def sample_policy(
        self, database_engine: ExtendedAsyncSAEngine
    ) -> AsyncGenerator[UserResourcePolicyData, None]:
        """Create a sample policy in the database for testing"""
        policy_name = "test-policy-sample"
        async with database_engine.begin_session() as db_sess:
            policy_row = UserResourcePolicyRow(
                name=policy_name,
                max_vfolder_count=10,
                max_quota_scope_size=1000000,
                max_session_count_per_model_session=5,
                max_customized_image_count=3,
            )
            db_sess.add(policy_row)
            await db_sess.flush()

        yield policy_row.to_dataclass()

        # Cleanup
        async with database_engine.begin_session() as db_sess:
            await db_sess.execute(
                sa.delete(UserResourcePolicyRow).where(UserResourcePolicyRow.name == policy_name)
            )

    @pytest.mark.asyncio
    async def test_create_policy(self, repository: UserResourcePolicyRepository) -> None:
        """Test creating a new user resource policy"""
        policy_name = "test-policy-create"
        max_vfolder_count = 10
        max_quota_scope_size = 1000000
        max_session_count_per_model_session = 5
        max_customized_image_count = 3

        policy_fields = {
            "name": policy_name,
            "max_vfolder_count": max_vfolder_count,
            "max_quota_scope_size": max_quota_scope_size,
            "max_session_count_per_model_session": max_session_count_per_model_session,
            "max_customized_image_count": max_customized_image_count,
        }

        try:
            result = await repository.create(policy_fields)

            assert isinstance(result, UserResourcePolicyData)
            assert result.name == "test-policy-create"
            assert result.max_vfolder_count == max_vfolder_count
            assert result.max_quota_scope_size == max_quota_scope_size
            assert result.max_session_count_per_model_session == max_session_count_per_model_session
            assert result.max_customized_image_count == max_customized_image_count
        finally:
            # Cleanup
            await repository.delete(policy_name)

    @pytest.mark.asyncio
    async def test_get_by_name_success(
        self, repository: UserResourcePolicyRepository, sample_policy: UserResourcePolicyData
    ) -> None:
        """Test getting a policy by name successfully"""
        result = await repository.get_by_name(sample_policy.name)

        assert isinstance(result, UserResourcePolicyData)
        assert result.name == sample_policy.name
        assert result.max_vfolder_count == sample_policy.max_vfolder_count
        assert result.max_quota_scope_size == sample_policy.max_quota_scope_size

    @pytest.mark.asyncio
    async def test_get_by_name_not_found(self, repository: UserResourcePolicyRepository) -> None:
        """Test getting a policy by name when it doesn't exist"""
        with pytest.raises(UserResourcePolicyNotFound):
            await repository.get_by_name("non-existing")

    @pytest.mark.asyncio
    async def test_update_policy_success(
        self, repository: UserResourcePolicyRepository, sample_policy: UserResourcePolicyData
    ) -> None:
        """Test updating a policy successfully"""
        updated_vfolder_count = 20
        updated_quota_size = 2000000

        update_fields = {
            "max_vfolder_count": updated_vfolder_count,
            "max_quota_scope_size": updated_quota_size,
        }

        result = await repository.update(sample_policy.name, update_fields)

        assert isinstance(result, UserResourcePolicyData)
        assert result.name == sample_policy.name
        assert result.max_vfolder_count == updated_vfolder_count
        assert result.max_quota_scope_size == updated_quota_size

    @pytest.mark.asyncio
    async def test_update_policy_not_found(self, repository: UserResourcePolicyRepository) -> None:
        """Test updating a policy that doesn't exist"""
        with pytest.raises(UserResourcePolicyNotFound):
            await repository.update("non-existing", {"max_vfolder_count": 20})

    @pytest.mark.asyncio
    async def test_delete_policy_success(
        self, repository: UserResourcePolicyRepository, sample_policy: UserResourcePolicyData
    ) -> None:
        """Test deleting a policy successfully"""
        result = await repository.delete(sample_policy.name)

        assert isinstance(result, UserResourcePolicyData)
        assert result.name == sample_policy.name

        # Verify it's actually deleted
        with pytest.raises(UserResourcePolicyNotFound):
            await repository.get_by_name(sample_policy.name)

    @pytest.mark.asyncio
    async def test_delete_policy_not_found(self, repository: UserResourcePolicyRepository) -> None:
        """Test deleting a policy that doesn't exist"""
        with pytest.raises(UserResourcePolicyNotFound):
            await repository.delete("non-existing")

    @pytest.mark.asyncio
    async def test_create_and_get_roundtrip(self, repository: UserResourcePolicyRepository) -> None:
        """Test creating a policy and retrieving it"""
        policy_fields = {
            "name": "test-policy-roundtrip",
            "max_vfolder_count": 15,
            "max_quota_scope_size": 500000,
            "max_session_count_per_model_session": 10,
            "max_customized_image_count": 5,
        }

        try:
            created = await repository.create(policy_fields)
            retrieved = await repository.get_by_name(created.name)

            assert created.name == retrieved.name
            assert created.max_vfolder_count == retrieved.max_vfolder_count
            assert created.max_quota_scope_size == retrieved.max_quota_scope_size
            assert (
                created.max_session_count_per_model_session
                == retrieved.max_session_count_per_model_session
            )
            assert created.max_customized_image_count == retrieved.max_customized_image_count
        finally:
            # Cleanup
            try:
                await repository.delete("test-policy-roundtrip")
            except UserResourcePolicyNotFound:
                pass
