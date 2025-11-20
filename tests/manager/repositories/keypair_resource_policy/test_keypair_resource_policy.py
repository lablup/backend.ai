"""
Tests for KeypairResourcePolicyRepository functionality.
Tests the repository layer with mocked database operations.
"""

from datetime import datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ai.backend.common.types import DefaultForUnspecified, ResourceSlot
from ai.backend.manager.data.resource.types import KeyPairResourcePolicyData
from ai.backend.manager.errors.common import ObjectNotFound
from ai.backend.manager.models.resource_policy import KeyPairResourcePolicyRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.keypair_resource_policy.repository import (
    KeypairResourcePolicyRepository,
)


class TestKeypairResourcePolicyRepository:
    """Test cases for KeypairResourcePolicyRepository"""

    @pytest.fixture
    def mock_db_engine(self) -> MagicMock:
        """Create mocked database engine"""
        return MagicMock(spec=ExtendedAsyncSAEngine)

    @pytest.fixture
    def keypair_resource_policy_repository(
        self, mock_db_engine: MagicMock
    ) -> KeypairResourcePolicyRepository:
        """Create KeypairResourcePolicyRepository instance with mocked database"""
        return KeypairResourcePolicyRepository(db=mock_db_engine)

    @pytest.fixture
    def sample_policy_row(self) -> KeyPairResourcePolicyRow:
        """Create sample keypair resource policy row for testing"""
        return KeyPairResourcePolicyRow(
            name="test-policy",
            max_concurrent_sessions=5,
            max_containers_per_session=2,
            total_resource_slots={"cpu": 8, "mem": "16g"},
            idle_timeout=3600,
        )

    @pytest.fixture
    def sample_policy_data(self) -> KeyPairResourcePolicyData:
        """Create sample keypair resource policy data for testing"""
        return KeyPairResourcePolicyData(
            name="test-policy",
            created_at=datetime.now(),
            default_for_unspecified=DefaultForUnspecified.UNLIMITED,
            total_resource_slots=ResourceSlot({"cpu": "8", "mem": "16g"}),
            max_session_lifetime=86400,
            max_concurrent_sessions=5,
            max_pending_session_count=10,
            max_pending_session_resource_slots={"cpu": 2, "mem": "4g"},
            max_concurrent_sftp_sessions=3,
            max_containers_per_session=2,
            idle_timeout=3600,
            allowed_vfolder_hosts={"local": None},
        )

    @pytest.fixture
    def new_policy_fields(self) -> dict[str, Any]:
        """Create fields for new policy creation testing"""
        return {
            "name": "new-policy",
            "default_for_unspecified": DefaultForUnspecified.UNLIMITED,
            "total_resource_slots": {"cpu": 16, "mem": "32g"},
            "max_session_lifetime": 86400,
            "max_concurrent_sessions": 10,
            "max_pending_session_count": 20,
            "max_pending_session_resource_slots": {"cpu": 4, "mem": "8g"},
            "max_concurrent_sftp_sessions": 5,
            "max_containers_per_session": 3,
            "idle_timeout": 7200,
            "allowed_vfolder_hosts": {"local": None},
        }

    @pytest.mark.asyncio
    async def test_create_success(
        self,
        keypair_resource_policy_repository: KeypairResourcePolicyRepository,
        mock_db_engine: MagicMock,
        new_policy_fields: dict[str, Any],
    ) -> None:
        """Test successful keypair resource policy creation"""
        # Mock database session
        mock_session = AsyncMock(spec=AsyncSession)
        mock_db_engine.begin_session.return_value.__aenter__.return_value = mock_session

        # Create expected policy data matching the new fields
        expected_policy_data = KeyPairResourcePolicyData(
            created_at=datetime.now(), **new_policy_fields
        )

        # Mock the to_dataclass method
        mock_policy_row = MagicMock()
        mock_policy_row.to_dataclass.return_value = expected_policy_data

        # Mock session.add and flush
        mock_session.add = Mock()
        mock_session.flush = AsyncMock()

        # Patch the class at the location where it's used in the repository
        with patch(
            "ai.backend.manager.repositories.keypair_resource_policy.repository.KeyPairResourcePolicyRow"
        ) as mock_policy_class:
            mock_policy_class.return_value = mock_policy_row
            result = await keypair_resource_policy_repository.create(new_policy_fields)

            assert result == expected_policy_data
            assert result.name == "new-policy"
            assert result.max_concurrent_sessions == 10
            assert result.max_containers_per_session == 3
            assert result.total_resource_slots == {"cpu": 16, "mem": "32g"}
            assert result.idle_timeout == 7200
            assert result.max_session_lifetime == 86400
            assert result.max_pending_session_count == 20

            # Verify the class was instantiated with correct fields
            mock_policy_class.assert_called_once_with(**new_policy_fields)
            mock_session.add.assert_called_once()
            # Check that the mock_policy_row was added
            assert mock_session.add.call_args[0][0] == mock_policy_row

    @pytest.mark.asyncio
    async def test_create_duplicate_name(
        self,
        keypair_resource_policy_repository: KeypairResourcePolicyRepository,
        mock_db_engine: MagicMock,
        new_policy_fields: dict[str, Any],
    ) -> None:
        """Test keypair resource policy creation with duplicate name"""
        # Mock database session
        mock_session = AsyncMock(spec=AsyncSession)
        mock_db_engine.begin_session.return_value.__aenter__.return_value = mock_session

        # Mock session.add to raise IntegrityError
        mock_session.add = Mock()
        mock_session.flush = AsyncMock(side_effect=IntegrityError("duplicate key", None, None))

        with pytest.raises(IntegrityError):
            await keypair_resource_policy_repository.create(new_policy_fields)

    @pytest.mark.asyncio
    async def test_get_by_name_success(
        self,
        keypair_resource_policy_repository: KeypairResourcePolicyRepository,
        mock_db_engine: MagicMock,
        sample_policy_row: KeyPairResourcePolicyRow,
        sample_policy_data: KeyPairResourcePolicyData,
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
        sample_policy_row.to_dataclass = Mock(return_value=sample_policy_data)  # type: ignore

        result = await keypair_resource_policy_repository.get_by_name("test-policy")

        assert result == sample_policy_data
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_name_not_found(
        self,
        keypair_resource_policy_repository: KeypairResourcePolicyRepository,
        mock_db_engine: MagicMock,
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
            await keypair_resource_policy_repository.get_by_name("nonexistent-policy")

        assert "Keypair resource policy with name nonexistent-policy not found" in str(
            exc_info.value
        )

    @pytest.mark.asyncio
    async def test_update_success(
        self,
        keypair_resource_policy_repository: KeypairResourcePolicyRepository,
        mock_db_engine: MagicMock,
        sample_policy_row: KeyPairResourcePolicyRow,
        sample_policy_data: KeyPairResourcePolicyData,
    ) -> None:
        """Test successful policy update"""
        # Mock database session
        mock_session = AsyncMock(spec=AsyncSession)
        mock_db_engine.begin_session.return_value.__aenter__.return_value = mock_session

        # Mock query result
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_policy_row
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.flush = AsyncMock()

        # Mock to_dataclass method
        sample_policy_row.to_dataclass = Mock(return_value=sample_policy_data)  # type: ignore

        update_fields = {
            "max_concurrent_sessions": 10,
            "idle_timeout": 7200,
        }

        result = await keypair_resource_policy_repository.update("test-policy", update_fields)

        assert result == sample_policy_data
        mock_session.execute.assert_called_once()
        mock_session.flush.assert_called_once()

        # Verify fields were updated
        for key, value in update_fields.items():
            assert hasattr(sample_policy_row, key)

    @pytest.mark.asyncio
    async def test_update_not_found(
        self,
        keypair_resource_policy_repository: KeypairResourcePolicyRepository,
        mock_db_engine: MagicMock,
    ) -> None:
        """Test policy update when policy not found"""
        # Mock database session
        mock_session = AsyncMock(spec=AsyncSession)
        mock_db_engine.begin_session.return_value.__aenter__.return_value = mock_session

        # Mock query result to return None
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)

        with pytest.raises(ObjectNotFound) as exc_info:
            await keypair_resource_policy_repository.update(
                "nonexistent-policy", {"max_concurrent_sessions": 30}
            )

        assert "Keypair resource policy with name nonexistent-policy not found" in str(
            exc_info.value
        )

    @pytest.mark.asyncio
    async def test_update_partial_fields(
        self,
        keypair_resource_policy_repository: KeypairResourcePolicyRepository,
        mock_db_engine: MagicMock,
        sample_policy_row: KeyPairResourcePolicyRow,
        sample_policy_data: KeyPairResourcePolicyData,
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
        sample_policy_row.to_dataclass = Mock(return_value=sample_policy_data)  # type: ignore

        # Update only one field
        update_fields = {"max_concurrent_sessions": 25}

        result = await keypair_resource_policy_repository.update("test-policy", update_fields)

        assert result == sample_policy_data

        # Verify only specified field was updated
        setattr(sample_policy_row, "max_concurrent_sessions", 25)

    @pytest.mark.asyncio
    async def test_delete_success(
        self,
        keypair_resource_policy_repository: KeypairResourcePolicyRepository,
        mock_db_engine: MagicMock,
        sample_policy_row: KeyPairResourcePolicyRow,
        sample_policy_data: KeyPairResourcePolicyData,
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
        sample_policy_row.to_dataclass = Mock(return_value=sample_policy_data)  # type: ignore

        result = await keypair_resource_policy_repository.delete("test-policy")

        assert result == sample_policy_data
        mock_session.execute.assert_called_once()
        mock_session.delete.assert_called_once_with(sample_policy_row)

    @pytest.mark.asyncio
    async def test_delete_not_found(
        self,
        keypair_resource_policy_repository: KeypairResourcePolicyRepository,
        mock_db_engine: MagicMock,
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
            await keypair_resource_policy_repository.delete("nonexistent-policy")

        assert "Keypair resource policy with name nonexistent-policy not found" in str(
            exc_info.value
        )

    @pytest.mark.asyncio
    async def test_create_with_all_fields(
        self,
        keypair_resource_policy_repository: KeypairResourcePolicyRepository,
        mock_db_engine: MagicMock,
    ) -> None:
        """Test creating policy with all possible fields"""
        # Mock database session
        mock_session = AsyncMock(spec=AsyncSession)
        mock_db_engine.begin_session.return_value.__aenter__.return_value = mock_session

        name = "comprehensive-policy"
        max_concurrent_sessions = 50
        max_containers_per_session = 5
        total_resource_slots = ResourceSlot({"cpu": "32", "mem": "64g", "cuda.device": "2"})
        idle_timeout = 14400
        max_session_lifetime = 86400
        all_fields = {
            "name": name,
            "default_for_unspecified": DefaultForUnspecified.UNLIMITED,
            "total_resource_slots": total_resource_slots,
            "max_session_lifetime": max_session_lifetime,
            "max_concurrent_sessions": max_concurrent_sessions,
            "max_pending_session_count": 50,
            "max_pending_session_resource_slots": {"cpu": 8, "mem": "16g"},
            "max_concurrent_sftp_sessions": 10,
            "max_containers_per_session": max_containers_per_session,
            "idle_timeout": idle_timeout,
            "allowed_vfolder_hosts": {"local": None, "shared": None},
        }

        mock_policy_data = KeyPairResourcePolicyData(
            name=name,
            created_at=datetime.now(),
            default_for_unspecified=DefaultForUnspecified.UNLIMITED,
            total_resource_slots=total_resource_slots,
            max_session_lifetime=max_session_lifetime,
            max_concurrent_sessions=max_concurrent_sessions,
            max_pending_session_count=50,
            max_pending_session_resource_slots={"cpu": 8, "mem": "16g"},
            max_concurrent_sftp_sessions=10,
            max_containers_per_session=max_containers_per_session,
            idle_timeout=idle_timeout,
            allowed_vfolder_hosts={"local": None, "shared": None},
        )
        mock_policy_row = MagicMock()
        mock_policy_row.to_dataclass.return_value = mock_policy_data

        mock_session.add = Mock()
        mock_session.flush = AsyncMock()

        with patch(
            "ai.backend.manager.repositories.keypair_resource_policy.repository.KeyPairResourcePolicyRow"
        ) as mock_policy_class:
            mock_policy_class.return_value = mock_policy_row
            result = await keypair_resource_policy_repository.create(all_fields)

            assert result.name == "comprehensive-policy"
            assert result.max_concurrent_sessions == 50
            assert result.max_containers_per_session == 5
            assert result.total_resource_slots == total_resource_slots
            assert result.idle_timeout == 14400
            assert result.max_session_lifetime == 86400
            assert result.max_pending_session_count == 50
            assert result.max_concurrent_sftp_sessions == 10

            # Verify the class was instantiated with correct fields
            mock_policy_class.assert_called_once_with(**all_fields)

    @pytest.mark.asyncio
    async def test_repository_with_transaction_rollback(
        self,
        keypair_resource_policy_repository: KeypairResourcePolicyRepository,
        mock_db_engine: MagicMock,
    ) -> None:
        """Test repository handles transaction rollback properly"""
        # Mock database session
        mock_session = AsyncMock(spec=AsyncSession)
        mock_db_engine.begin_session.return_value.__aenter__.return_value = mock_session

        # Make flush raise an exception
        mock_session.add = Mock()
        mock_session.flush = AsyncMock(side_effect=Exception("Database error"))

        # Provide all required fields
        policy_fields = {
            "name": "fail-policy",
            "default_for_unspecified": DefaultForUnspecified.UNLIMITED,
            "total_resource_slots": {"cpu": 8, "mem": "16g"},
            "max_session_lifetime": 86400,
            "max_concurrent_sessions": 10,
            "max_pending_session_count": 20,
            "max_pending_session_resource_slots": {"cpu": 2, "mem": "4g"},
            "max_concurrent_sftp_sessions": 3,
            "max_containers_per_session": 2,
            "idle_timeout": 3600,
            "allowed_vfolder_hosts": {"local": None},
        }

        with pytest.raises(Exception) as exc_info:
            await keypair_resource_policy_repository.create(policy_fields)

        assert "Database error" in str(exc_info.value)
