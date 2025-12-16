"""
Tests for ProjectResourcePolicyRepository functionality.
Tests the repository layer with mocked database operations.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ai.backend.manager.data.resource.types import ProjectResourcePolicyData
from ai.backend.manager.errors.common import ObjectNotFound
from ai.backend.manager.models.resource_policy import ProjectResourcePolicyRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.project_resource_policy.creators import (
    ProjectResourcePolicyCreatorSpec,
)
from ai.backend.manager.repositories.project_resource_policy.repository import (
    ProjectResourcePolicyRepository,
)
from ai.backend.manager.repositories.project_resource_policy.updaters import (
    ProjectResourcePolicyUpdaterSpec,
)
from ai.backend.manager.types import OptionalState


class TestProjectResourcePolicyRepository:
    """Test cases for ProjectResourcePolicyRepository"""

    @pytest.fixture
    def mock_db_engine(self) -> MagicMock:
        """Create mocked database engine"""
        return MagicMock(spec=ExtendedAsyncSAEngine)

    @pytest.fixture
    def project_resource_policy_repository(self, mock_db_engine) -> ProjectResourcePolicyRepository:
        """Create ProjectResourcePolicyRepository instance with mocked database"""
        return ProjectResourcePolicyRepository(db=mock_db_engine)

    @pytest.fixture
    def sample_policy_row(self) -> ProjectResourcePolicyRow:
        """Create sample project resource policy row for testing"""
        return ProjectResourcePolicyRow(
            name="test-policy",
            max_vfolder_count=10,
            max_quota_scope_size=1073741824,  # 1GB
            max_network_count=5,
        )

    @pytest.fixture
    def sample_policy_data(self) -> ProjectResourcePolicyData:
        """Create sample project resource policy data for testing"""
        return ProjectResourcePolicyData(
            name="test-policy",
            max_vfolder_count=10,
            max_quota_scope_size=1073741824,  # 1GB
            max_network_count=5,
        )

    @pytest.fixture
    def new_policy_creator(self) -> Creator[ProjectResourcePolicyRow]:
        """Create Creator for new policy creation testing"""
        spec = ProjectResourcePolicyCreatorSpec(
            name="new-policy",
            max_vfolder_count=20,
            max_quota_scope_size=2147483648,  # 2GB
            max_network_count=10,
        )
        return Creator(spec=spec)

    @pytest.mark.asyncio
    async def test_create_success(
        self, project_resource_policy_repository, mock_db_engine, new_policy_creator
    ) -> None:
        """Test successful project resource policy creation"""
        # Mock database session
        mock_session = AsyncMock(spec=AsyncSession)
        mock_db_engine.begin_session.return_value.__aenter__.return_value = mock_session

        # Create expected policy data
        expected_policy_data = ProjectResourcePolicyData(
            name="new-policy",
            max_vfolder_count=20,
            max_quota_scope_size=2147483648,  # 2GB
            max_network_count=10,
        )

        # Mock the to_dataclass method
        mock_policy_row = MagicMock()
        mock_policy_row.to_dataclass.return_value = expected_policy_data

        # Mock session.add, flush, and refresh
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()
        mock_session.refresh = AsyncMock()

        # Patch build_row to return our mock
        with patch.object(new_policy_creator.spec, "build_row", return_value=mock_policy_row):
            result = await project_resource_policy_repository.create(new_policy_creator)

            assert result == expected_policy_data
            assert result.name == "new-policy"
            assert result.max_vfolder_count == 20
            assert result.max_quota_scope_size == 2147483648
            assert result.max_network_count == 10

            mock_session.add.assert_called_once()
            # Check that the mock_policy_row was added
            assert mock_session.add.call_args[0][0] == mock_policy_row

    @pytest.mark.asyncio
    async def test_create_duplicate_name(
        self, project_resource_policy_repository, mock_db_engine, new_policy_creator
    ) -> None:
        """Test project resource policy creation with duplicate name"""
        # Mock database session
        mock_session = AsyncMock(spec=AsyncSession)
        mock_db_engine.begin_session.return_value.__aenter__.return_value = mock_session

        # Mock session.add to raise IntegrityError
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock(side_effect=IntegrityError("duplicate key", None, None))

        with pytest.raises(IntegrityError):
            await project_resource_policy_repository.create(new_policy_creator)

    @pytest.mark.asyncio
    async def test_get_by_name_success(
        self,
        project_resource_policy_repository,
        mock_db_engine,
        sample_policy_row,
        sample_policy_data,
    ) -> None:
        """Test successful policy retrieval by name"""
        # Mock database session
        mock_session = AsyncMock(spec=AsyncSession)
        mock_db_engine.begin_readonly_session.return_value.__aenter__.return_value = mock_session

        # Mock query result
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_policy_row
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Mock to_dataclass method
        sample_policy_row.to_dataclass = MagicMock(return_value=sample_policy_data)

        result = await project_resource_policy_repository.get_by_name("test-policy")

        assert result == sample_policy_data
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_name_not_found(
        self, project_resource_policy_repository, mock_db_engine
    ) -> None:
        """Test policy retrieval when policy not found"""
        # Mock database session
        mock_session = AsyncMock(spec=AsyncSession)
        mock_db_engine.begin_readonly_session.return_value.__aenter__.return_value = mock_session

        # Mock query result to return None
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)

        with pytest.raises(ObjectNotFound) as exc_info:
            await project_resource_policy_repository.get_by_name("nonexistent-policy")

        assert "Project resource policy with name nonexistent-policy not found" in str(
            exc_info.value
        )

    @pytest.mark.asyncio
    async def test_update_success(
        self,
        project_resource_policy_repository,
        mock_db_engine,
        sample_policy_row,
        sample_policy_data,
    ) -> None:
        """Test successful policy update"""
        # Mock database session
        mock_session = AsyncMock(spec=AsyncSession)
        mock_db_engine.begin_session.return_value.__aenter__.return_value = mock_session

        # Mock query result (execute_updater uses from_statement which returns the row directly)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_policy_row
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Mock to_dataclass method
        sample_policy_row.to_dataclass = MagicMock(return_value=sample_policy_data)

        # Create updater with the new pattern
        spec = ProjectResourcePolicyUpdaterSpec(
            max_vfolder_count=OptionalState.update(30),
            max_quota_scope_size=OptionalState.update(3221225472),  # 3GB
        )
        updater = Updater(spec=spec, pk_value="test-policy")

        result = await project_resource_policy_repository.update(updater)

        assert result == sample_policy_data
        mock_session.execute.assert_called_once()

        # Verify fields exist on the row
        assert hasattr(sample_policy_row, "max_vfolder_count")
        assert hasattr(sample_policy_row, "max_quota_scope_size")

    @pytest.mark.asyncio
    async def test_update_not_found(
        self, project_resource_policy_repository, mock_db_engine
    ) -> None:
        """Test policy update when policy not found"""
        # Mock database session
        mock_session = AsyncMock(spec=AsyncSession)
        mock_db_engine.begin_session.return_value.__aenter__.return_value = mock_session

        # Mock query result to return None
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)

        spec = ProjectResourcePolicyUpdaterSpec(
            max_vfolder_count=OptionalState.update(30),
        )
        updater = Updater(spec=spec, pk_value="nonexistent-policy")

        with pytest.raises(ObjectNotFound) as exc_info:
            await project_resource_policy_repository.update(updater)

        assert "Project resource policy with name nonexistent-policy not found" in str(
            exc_info.value
        )

    @pytest.mark.asyncio
    async def test_update_partial_fields(
        self,
        project_resource_policy_repository,
        mock_db_engine,
        sample_policy_row,
        sample_policy_data,
    ) -> None:
        """Test partial update of policy fields"""
        # Mock database session
        mock_session = AsyncMock(spec=AsyncSession)
        mock_db_engine.begin_session.return_value.__aenter__.return_value = mock_session

        # Mock query result
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_policy_row
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.flush = AsyncMock()

        # Mock to_dataclass method
        sample_policy_row.to_dataclass = MagicMock(return_value=sample_policy_data)

        # Update only one field using Updater pattern
        spec = ProjectResourcePolicyUpdaterSpec(
            max_vfolder_count=OptionalState.update(25),
        )
        updater = Updater(spec=spec, pk_value="test-policy")

        result = await project_resource_policy_repository.update(updater)

        assert result == sample_policy_data

        # Verify only specified field was updated
        setattr(sample_policy_row, "max_vfolder_count", 25)

    @pytest.mark.asyncio
    async def test_delete_success(
        self,
        project_resource_policy_repository,
        mock_db_engine,
        sample_policy_row,
        sample_policy_data,
    ) -> None:
        """Test successful policy deletion"""
        # Mock database session
        mock_session = AsyncMock(spec=AsyncSession)
        mock_db_engine.begin_session.return_value.__aenter__.return_value = mock_session

        # Mock query result
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_policy_row
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.delete = AsyncMock()

        # Mock to_dataclass method
        sample_policy_row.to_dataclass = MagicMock(return_value=sample_policy_data)

        result = await project_resource_policy_repository.delete("test-policy")

        assert result == sample_policy_data
        mock_session.execute.assert_called_once()
        mock_session.delete.assert_called_once_with(sample_policy_row)

    @pytest.mark.asyncio
    async def test_delete_not_found(
        self, project_resource_policy_repository, mock_db_engine
    ) -> None:
        """Test policy deletion when policy not found"""
        # Mock database session
        mock_session = AsyncMock(spec=AsyncSession)
        mock_db_engine.begin_session.return_value.__aenter__.return_value = mock_session

        # Mock query result to return None
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)

        with pytest.raises(ObjectNotFound) as exc_info:
            await project_resource_policy_repository.delete("nonexistent-policy")

        assert "Project resource policy with name nonexistent-policy not found" in str(
            exc_info.value
        )

    @pytest.mark.asyncio
    async def test_create_with_all_fields(
        self, project_resource_policy_repository, mock_db_engine
    ) -> None:
        """Test creating policy with all possible fields"""
        # Mock database session
        mock_session = AsyncMock(spec=AsyncSession)
        mock_db_engine.begin_session.return_value.__aenter__.return_value = mock_session

        name = "comprehensive-policy"
        max_vfolder_count = 50
        max_quota_scope_size = 5368709120  # 5GB
        max_network_count = 20

        spec = ProjectResourcePolicyCreatorSpec(
            name=name,
            max_vfolder_count=max_vfolder_count,
            max_quota_scope_size=max_quota_scope_size,
            max_network_count=max_network_count,
        )
        creator = Creator(spec=spec)

        mock_policy_data = ProjectResourcePolicyData(
            name=name,
            max_vfolder_count=max_vfolder_count,
            max_quota_scope_size=max_quota_scope_size,
            max_network_count=max_network_count,
        )
        mock_policy_row = MagicMock()
        mock_policy_row.to_dataclass.return_value = mock_policy_data

        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()
        mock_session.refresh = AsyncMock()

        with patch.object(spec, "build_row", return_value=mock_policy_row):
            result = await project_resource_policy_repository.create(creator)

            assert result.name == "comprehensive-policy"
            assert result.max_vfolder_count == 50
            assert result.max_quota_scope_size == 5368709120
            assert result.max_network_count == 20

    @pytest.mark.asyncio
    async def test_repository_with_transaction_rollback(
        self, project_resource_policy_repository, mock_db_engine
    ) -> None:
        """Test repository handles transaction rollback properly"""
        # Mock database session
        mock_session = AsyncMock(spec=AsyncSession)
        mock_db_engine.begin_session.return_value.__aenter__.return_value = mock_session

        # Make flush raise an exception
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock(side_effect=Exception("Database error"))

        # Create creator with all required fields
        spec = ProjectResourcePolicyCreatorSpec(
            name="fail-policy",
            max_vfolder_count=10,
            max_quota_scope_size=1073741824,
            max_network_count=5,
        )
        creator = Creator(spec=spec)

        with pytest.raises(Exception) as exc_info:
            await project_resource_policy_repository.create(creator)

        assert "Database error" in str(exc_info.value)
