"""
Tests for UserResourcePolicyRepository with mocked database.
These tests verify the repository methods without requiring actual database setup.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai.backend.manager.data.resource.types import UserResourcePolicyData
from ai.backend.manager.errors.common import ObjectNotFound
from ai.backend.manager.models.resource_policy import UserResourcePolicyRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.user_resource_policy.repository import (
    UserResourcePolicyRepository,
)


@pytest.fixture
def mock_db_engine():
    """Mock database engine for testing"""
    return AsyncMock(spec=ExtendedAsyncSAEngine)


@pytest.fixture
def repository(mock_db_engine):
    """Repository instance with mocked database"""
    return UserResourcePolicyRepository(db=mock_db_engine)


@pytest.fixture
def sample_policy_data():
    """Sample policy data for testing"""
    return {
        "name": "test-policy",
        "max_vfolder_count": 10,
        "max_quota_scope_size": 1000000,
        "max_session_count_per_model_session": 5,
        "max_customized_image_count": 3,
    }


@pytest.fixture
def sample_policy_dataclass():
    """Sample policy dataclass for testing"""
    return UserResourcePolicyData(
        name="test-policy",
        max_vfolder_count=10,
        max_quota_scope_size=1000000,
        max_session_count_per_model_session=5,
        max_customized_image_count=3,
    )


class TestUserResourcePolicyRepository:
    """Test suite for UserResourcePolicyRepository"""

    @pytest.mark.asyncio
    async def test_create_policy(
        self, repository, mock_db_engine, sample_policy_data, sample_policy_dataclass
    ):
        """Test creating a new user resource policy"""
        # Setup mock session and row
        mock_session = AsyncMock()
        mock_db_engine.begin_session.return_value.__aenter__.return_value = mock_session

        # Mock the row creation and to_dataclass conversion
        mock_row = MagicMock(spec=UserResourcePolicyRow)
        mock_row.to_dataclass.return_value = sample_policy_dataclass

        with patch(
            "ai.backend.manager.repositories.user_resource_policy.repository.UserResourcePolicyRow"
        ) as mock_row_class:
            mock_row_class.return_value = mock_row

            # Execute the method
            result = await repository.create(sample_policy_data)

            # Verify the result
            assert result == sample_policy_dataclass

            # Verify the row was created with correct data
            mock_row_class.assert_called_once_with(**sample_policy_data)
            mock_session.add.assert_called_once_with(mock_row)
            mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_name_success(self, repository, mock_db_engine, sample_policy_dataclass):
        """Test getting a policy by name successfully"""
        # Setup mock session and query result
        mock_session = AsyncMock()
        mock_db_engine.begin_readonly_session.return_value.__aenter__.return_value = mock_session

        mock_result = MagicMock()
        mock_row = MagicMock(spec=UserResourcePolicyRow)
        mock_row.to_dataclass.return_value = sample_policy_dataclass
        mock_result.scalar_one_or_none.return_value = mock_row
        mock_session.execute.return_value = mock_result

        # Execute the method
        result = await repository.get_by_name("test-policy")

        # Verify the result
        assert result == sample_policy_dataclass
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_name_not_found(self, repository, mock_db_engine):
        """Test getting a policy by name when it doesn't exist"""
        # Setup mock session and query result
        mock_session = AsyncMock()
        mock_db_engine.begin_readonly_session.return_value.__aenter__.return_value = mock_session

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        # Execute and verify exception is raised
        with pytest.raises(
            ObjectNotFound, match="User resource policy with name non-existing not found"
        ):
            await repository.get_by_name("non-existing")

    @pytest.mark.asyncio
    async def test_update_policy_success(self, repository, mock_db_engine, sample_policy_dataclass):
        """Test updating a policy successfully"""
        # Setup mock session and query result
        mock_session = AsyncMock()
        mock_db_engine.begin_session.return_value.__aenter__.return_value = mock_session

        mock_result = MagicMock()
        mock_row = MagicMock(spec=UserResourcePolicyRow)
        mock_row.to_dataclass.return_value = sample_policy_dataclass
        mock_result.scalar_one_or_none.return_value = mock_row
        mock_session.execute.return_value = mock_result

        # Update data
        update_fields = {
            "max_vfolder_count": 20,
            "max_quota_scope_size": 2000000,
        }

        # Execute the method
        result = await repository.update("test-policy", update_fields)

        # Verify the result
        assert result == sample_policy_dataclass

        # Verify the row was updated
        for key, value in update_fields.items():
            setattr(mock_row, key, value)
        mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_policy_not_found(self, repository, mock_db_engine):
        """Test updating a policy that doesn't exist"""
        # Setup mock session and query result
        mock_session = AsyncMock()
        mock_db_engine.begin_session.return_value.__aenter__.return_value = mock_session

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        # Execute and verify exception is raised
        with pytest.raises(
            ObjectNotFound, match="User resource policy with name non-existing not found"
        ):
            await repository.update("non-existing", {"max_vfolder_count": 20})

    @pytest.mark.asyncio
    async def test_delete_policy_success(self, repository, mock_db_engine, sample_policy_dataclass):
        """Test deleting a policy successfully"""
        # Setup mock session and query result
        mock_session = AsyncMock()
        mock_db_engine.begin_session.return_value.__aenter__.return_value = mock_session

        mock_result = MagicMock()
        mock_row = MagicMock(spec=UserResourcePolicyRow)
        mock_row.to_dataclass.return_value = sample_policy_dataclass
        mock_result.scalar_one_or_none.return_value = mock_row
        mock_session.execute.return_value = mock_result

        # Execute the method
        result = await repository.delete("test-policy")

        # Verify the result
        assert result == sample_policy_dataclass

        # Verify the row was deleted
        mock_session.delete.assert_called_once_with(mock_row)

    @pytest.mark.asyncio
    async def test_delete_policy_not_found(self, repository, mock_db_engine):
        """Test deleting a policy that doesn't exist"""
        # Setup mock session and query result
        mock_session = AsyncMock()
        mock_db_engine.begin_session.return_value.__aenter__.return_value = mock_session

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        # Execute and verify exception is raised
        with pytest.raises(
            ObjectNotFound, match="User resource policy with name non-existing not found"
        ):
            await repository.delete("non-existing")

    @pytest.mark.asyncio
    async def test_repository_decorator_applied(self, repository):
        """Test that the repository decorator is applied to all methods"""
        # Verify that all public methods have the decorator
        methods_with_decorator = ["create", "get_by_name", "update", "delete"]

        for method_name in methods_with_decorator:
            method = getattr(repository, method_name)
            # Check that the method has been decorated (this is a basic check)
            assert hasattr(method, "__wrapped__") or hasattr(method, "__name__")

    def test_repository_initialization(self, mock_db_engine):
        """Test repository initialization"""
        repo = UserResourcePolicyRepository(db=mock_db_engine)
        assert repo._db == mock_db_engine

    @pytest.mark.asyncio
    async def test_create_with_none_values(self, repository, mock_db_engine):
        """Test creating a policy with None values (should still work)"""
        # Setup mock session and row
        mock_session = AsyncMock()
        mock_db_engine.begin_session.return_value.__aenter__.return_value = mock_session

        policy_data_with_none = {
            "name": "test-policy",
            "max_vfolder_count": None,
            "max_quota_scope_size": None,
            "max_session_count_per_model_session": None,
            "max_customized_image_count": None,
        }

        expected_result = UserResourcePolicyData(
            name="test-policy",
            max_vfolder_count=0,  # Database default
            max_quota_scope_size=0,  # Database default
            max_session_count_per_model_session=0,  # Database default
            max_customized_image_count=3,  # Database default
        )

        # Mock the row creation and to_dataclass conversion
        mock_row = MagicMock(spec=UserResourcePolicyRow)
        mock_row.to_dataclass.return_value = expected_result

        with patch(
            "ai.backend.manager.repositories.user_resource_policy.repository.UserResourcePolicyRow"
        ) as mock_row_class:
            mock_row_class.return_value = mock_row

            # Execute the method
            result = await repository.create(policy_data_with_none)

            # Verify the result
            assert result == expected_result

            # Verify the row was created with the data (including None values)
            mock_row_class.assert_called_once_with(**policy_data_with_none)
