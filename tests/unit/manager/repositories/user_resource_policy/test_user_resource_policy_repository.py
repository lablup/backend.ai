from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest

from ai.backend.common.exception import UserResourcePolicyNotFound
from ai.backend.manager.data.resource.types import UserResourcePolicyData
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.user_resource_policy.creators import (
    UserResourcePolicyCreatorSpec,
)
from ai.backend.manager.repositories.user_resource_policy.repository import (
    UserResourcePolicyRepository,
)
from ai.backend.manager.repositories.user_resource_policy.updaters import (
    UserResourcePolicyUpdaterSpec,
)
from ai.backend.manager.types import OptionalState
from ai.backend.testutils.db import with_tables


class TestUserResourcePolicyRepository:
    """Test suite for UserResourcePolicyRepository"""

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        """Database connection with tables created. TRUNCATE CASCADE handles cleanup."""
        async with with_tables(
            database_connection,
            [
                DomainRow,
                UserResourcePolicyRow,
                KeyPairResourcePolicyRow,
                UserRow,
                KeyPairRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def repository(
        self, db_with_cleanup: ExtendedAsyncSAEngine
    ) -> UserResourcePolicyRepository:
        """Repository instance with real database"""
        return UserResourcePolicyRepository(db=db_with_cleanup)

    @pytest.fixture
    async def sample_policy(
        self, db_with_cleanup: ExtendedAsyncSAEngine
    ) -> AsyncGenerator[UserResourcePolicyData, None]:
        """Create a sample policy in the database for testing"""
        policy_name = "test-policy-sample"
        async with db_with_cleanup.begin_session() as db_sess:
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

    @pytest.mark.asyncio
    async def test_create_policy(self, repository: UserResourcePolicyRepository) -> None:
        """Test creating a new user resource policy"""
        policy_name = "test-policy-create"
        max_vfolder_count = 10
        max_quota_scope_size = 1000000
        max_session_count_per_model_session = 5
        max_customized_image_count = 3

        spec = UserResourcePolicyCreatorSpec(
            name=policy_name,
            max_vfolder_count=max_vfolder_count,
            max_quota_scope_size=max_quota_scope_size,
            max_session_count_per_model_session=max_session_count_per_model_session,
            max_customized_image_count=max_customized_image_count,
        )

        result = await repository.create(Creator(spec=spec))
        assert isinstance(result, UserResourcePolicyData)
        assert result.name == "test-policy-create"
        assert result.max_vfolder_count == max_vfolder_count
        assert result.max_quota_scope_size == max_quota_scope_size
        assert result.max_session_count_per_model_session == max_session_count_per_model_session
        assert result.max_customized_image_count == max_customized_image_count

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
    @pytest.mark.parametrize(
        "updater_spec,expected_updates",
        [
            (
                UserResourcePolicyUpdaterSpec(
                    max_vfolder_count=OptionalState.update(20),
                    max_quota_scope_size=OptionalState.nop(),
                    max_session_count_per_model_session=OptionalState.nop(),
                    max_customized_image_count=OptionalState.nop(),
                ),
                UserResourcePolicyData(
                    name="test-policy",
                    max_vfolder_count=20,
                    max_quota_scope_size=1000000,  # unchanged
                    max_session_count_per_model_session=5,  # unchanged
                    max_customized_image_count=3,  # unchanged
                ),
            ),
            (
                UserResourcePolicyUpdaterSpec(
                    max_vfolder_count=OptionalState.update(20),
                    max_quota_scope_size=OptionalState.update(2000000),
                    max_session_count_per_model_session=OptionalState.nop(),
                    max_customized_image_count=OptionalState.nop(),
                ),
                UserResourcePolicyData(
                    name="test-policy",
                    max_vfolder_count=20,
                    max_quota_scope_size=2000000,
                    max_session_count_per_model_session=5,  # unchanged
                    max_customized_image_count=3,  # unchanged
                ),
            ),
            (
                UserResourcePolicyUpdaterSpec(
                    max_vfolder_count=OptionalState.update(25),
                    max_quota_scope_size=OptionalState.update(3000000),
                    max_session_count_per_model_session=OptionalState.update(10),
                    max_customized_image_count=OptionalState.update(7),
                ),
                UserResourcePolicyData(
                    name="test-policy",
                    max_vfolder_count=25,
                    max_quota_scope_size=3000000,
                    max_session_count_per_model_session=10,
                    max_customized_image_count=7,
                ),
            ),
            (
                UserResourcePolicyUpdaterSpec(
                    max_vfolder_count=OptionalState.update(15),
                    max_quota_scope_size=OptionalState.nop(),
                    max_session_count_per_model_session=OptionalState.update(8),
                    max_customized_image_count=OptionalState.nop(),
                ),
                UserResourcePolicyData(
                    name="test-policy",
                    max_vfolder_count=15,
                    max_quota_scope_size=1000000,  # unchanged
                    max_session_count_per_model_session=8,
                    max_customized_image_count=3,  # unchanged
                ),
            ),
        ],
    )
    async def test_update_policy_success(
        self,
        repository: UserResourcePolicyRepository,
        sample_policy: UserResourcePolicyData,
        updater_spec: UserResourcePolicyUpdaterSpec,
        expected_updates: UserResourcePolicyData,
    ) -> None:
        """Test updating a policy successfully with various field combinations"""
        updater = Updater(spec=updater_spec, pk_value=sample_policy.name)
        result = await repository.update(updater)

        assert isinstance(result, UserResourcePolicyData)
        assert result.name == sample_policy.name
        assert result.max_vfolder_count == expected_updates.max_vfolder_count
        assert result.max_quota_scope_size == expected_updates.max_quota_scope_size
        assert (
            result.max_session_count_per_model_session
            == expected_updates.max_session_count_per_model_session
        )
        assert result.max_customized_image_count == expected_updates.max_customized_image_count

    @pytest.mark.asyncio
    async def test_update_policy_not_found(self, repository: UserResourcePolicyRepository) -> None:
        """Test updating a policy that doesn't exist"""
        updater = Updater(
            spec=UserResourcePolicyUpdaterSpec(max_vfolder_count=OptionalState.update(20)),
            pk_value="non-existing",
        )
        with pytest.raises(UserResourcePolicyNotFound):
            await repository.update(updater)

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
        policy_name = "test-policy-roundtrip"
        max_vfolder_count = 15
        max_quota_scope_size = 500000
        max_session_count_per_model_session = 10
        max_customized_image_count = 5

        created = await repository.create(
            Creator(
                spec=UserResourcePolicyCreatorSpec(
                    name=policy_name,
                    max_vfolder_count=max_vfolder_count,
                    max_quota_scope_size=max_quota_scope_size,
                    max_session_count_per_model_session=max_session_count_per_model_session,
                    max_customized_image_count=max_customized_image_count,
                )
            )
        )
        retrieved = await repository.get_by_name(created.name)

        assert created.name == retrieved.name
        assert created.max_vfolder_count == retrieved.max_vfolder_count
        assert created.max_quota_scope_size == retrieved.max_quota_scope_size
        assert (
            created.max_session_count_per_model_session
            == retrieved.max_session_count_per_model_session
        )
        assert created.max_customized_image_count == retrieved.max_customized_image_count
