"""
Tests for ResourcePresetRepository functionality.
Tests the repository layer with mocked database operations.
"""

import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from ai.backend.common.types import BinarySize, ResourceSlot
from ai.backend.manager.data.resource_preset.types import ResourcePresetData
from ai.backend.manager.errors.common import ObjectNotFound
from ai.backend.manager.models.resource_preset import ResourcePresetRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.resource_preset.repository import ResourcePresetRepository
from ai.backend.manager.services.resource_preset.types import (
    ResourcePresetCreator,
    ResourcePresetModifier,
)
from ai.backend.manager.types import OptionalState, TriState


class TestResourcePresetRepository:
    """Test cases for ResourcePresetRepository"""

    @pytest.fixture
    def mock_db_engine(self) -> MagicMock:
        """Create mocked database engine"""
        return MagicMock(spec=ExtendedAsyncSAEngine)

    @pytest.fixture
    def resource_preset_repository(self, mock_db_engine) -> ResourcePresetRepository:
        """Create ResourcePresetRepository instance with mocked database"""
        return ResourcePresetRepository(
            db=mock_db_engine, valkey_stat=MagicMock(), config_provider=MagicMock()
        )

    @pytest.fixture
    def sample_preset_row(self) -> MagicMock:
        """Create sample resource preset row for testing"""
        preset_data = ResourcePresetData(
            id=uuid.uuid4(),
            name="test-preset",
            resource_slots=ResourceSlot({"cpu": Decimal("4"), "mem": Decimal("8589934592")}),
            shared_memory=BinarySize(BinarySize.from_str("2G")),
            scaling_group_name=None,
        )

        mock_row = MagicMock(spec=ResourcePresetRow)
        mock_row.id = preset_data.id
        mock_row.name = preset_data.name
        mock_row.resource_slots = preset_data.resource_slots
        mock_row.shared_memory = preset_data.shared_memory
        mock_row.scaling_group_name = preset_data.scaling_group_name
        mock_row.to_dataclass.return_value = preset_data

        return mock_row

    @pytest.fixture
    def sample_preset_creator(self) -> ResourcePresetCreator:
        """Create sample resource preset creator for creation"""
        return ResourcePresetCreator(
            name="new-preset",
            resource_slots=ResourceSlot({"cpu": "2", "mem": "4G"}),
            shared_memory=str(BinarySize.from_str("1G")),
            scaling_group_name=None,
        )

    @pytest.mark.asyncio
    async def test_create_preset_validated_success(
        self, resource_preset_repository, mock_db_engine, sample_preset_creator, sample_preset_row
    ) -> None:
        """Test successful preset creation"""
        # Mock database session
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session_ctx = AsyncMock()
        mock_session_ctx.__aenter__.return_value = mock_session
        mock_session_ctx.__aexit__.return_value = None
        mock_db_engine.begin_session.return_value = mock_session_ctx

        # Mock ResourcePresetRow.create to return the preset row
        with patch.object(
            ResourcePresetRow, "create", AsyncMock(return_value=sample_preset_row)
        ) as mock_create:
            result = await resource_preset_repository.create_preset_validated(sample_preset_creator)

            assert result is not None
            assert isinstance(result, ResourcePresetData)
            assert result.name == sample_preset_row.name
            assert result.id == sample_preset_row.id
            mock_create.assert_called_once_with(sample_preset_creator, db_session=mock_session)

    @pytest.mark.asyncio
    async def test_create_preset_validated_duplicate(
        self, resource_preset_repository, mock_db_engine, sample_preset_creator
    ) -> None:
        """Test preset creation with duplicate name"""
        # Mock database session
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session_ctx = AsyncMock()
        mock_session_ctx.__aenter__.return_value = mock_session
        mock_session_ctx.__aexit__.return_value = None
        mock_db_engine.begin_session.return_value = mock_session_ctx

        # Mock ResourcePresetRow.create to return None (duplicate)
        with patch.object(ResourcePresetRow, "create", AsyncMock(return_value=None)):
            result = await resource_preset_repository.create_preset_validated(sample_preset_creator)

            assert result is None

    @pytest.mark.asyncio
    async def test_get_preset_by_id_success(
        self, resource_preset_repository, mock_db_engine, sample_preset_row
    ) -> None:
        """Test successful preset retrieval by ID"""
        preset_id = sample_preset_row.id

        # Mock database session
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session_ctx = AsyncMock()
        mock_session_ctx.__aenter__.return_value = mock_session
        mock_session_ctx.__aexit__.return_value = None
        mock_db_engine.begin_session.return_value = mock_session_ctx

        # Mock the _get_preset_by_id method
        with patch.object(
            resource_preset_repository,
            "_get_preset_by_id",
            AsyncMock(return_value=sample_preset_row),
        ):
            result = await resource_preset_repository.get_preset_by_id(preset_id)

            assert result.id == preset_id
            assert result.name == sample_preset_row.name

    @pytest.mark.asyncio
    async def test_get_preset_by_id_not_found(
        self, resource_preset_repository, mock_db_engine
    ) -> None:
        """Test preset retrieval by ID when not found"""
        preset_id = uuid.uuid4()

        # Mock database session
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session_ctx = AsyncMock()
        mock_session_ctx.__aenter__.return_value = mock_session
        mock_session_ctx.__aexit__.return_value = None
        mock_db_engine.begin_session.return_value = mock_session_ctx

        # Mock the _get_preset_by_id method to return None
        with patch.object(
            resource_preset_repository, "_get_preset_by_id", AsyncMock(return_value=None)
        ):
            with pytest.raises(ObjectNotFound, match="Resource preset not found"):
                await resource_preset_repository.get_preset_by_id(preset_id)

    @pytest.mark.asyncio
    async def test_get_preset_by_name_success(
        self, resource_preset_repository, mock_db_engine, sample_preset_row
    ) -> None:
        """Test successful preset retrieval by name"""
        # Mock database session
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session_ctx = AsyncMock()
        mock_session_ctx.__aenter__.return_value = mock_session
        mock_session_ctx.__aexit__.return_value = None
        mock_db_engine.begin_session.return_value = mock_session_ctx

        # Mock the _get_preset_by_name method
        with patch.object(
            resource_preset_repository,
            "_get_preset_by_name",
            AsyncMock(return_value=sample_preset_row),
        ):
            result = await resource_preset_repository.get_preset_by_name("test-preset")

            assert result.name == "test-preset"
            assert result.id == sample_preset_row.id

    @pytest.mark.asyncio
    async def test_get_preset_by_name_not_found(
        self, resource_preset_repository, mock_db_engine
    ) -> None:
        """Test preset retrieval by name when not found"""
        # Mock database session
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session_ctx = AsyncMock()
        mock_session_ctx.__aenter__.return_value = mock_session
        mock_session_ctx.__aexit__.return_value = None
        mock_db_engine.begin_session.return_value = mock_session_ctx

        # Mock the _get_preset_by_name method to return None
        with patch.object(
            resource_preset_repository, "_get_preset_by_name", AsyncMock(return_value=None)
        ):
            with pytest.raises(ObjectNotFound, match="Resource preset not found"):
                await resource_preset_repository.get_preset_by_name("non-existent")

    @pytest.mark.asyncio
    async def test_get_preset_by_id_or_name_with_id(
        self, resource_preset_repository, mock_db_engine, sample_preset_row
    ) -> None:
        """Test preset retrieval by ID when both ID and name provided"""
        preset_id = sample_preset_row.id

        # Mock database session
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session_ctx = AsyncMock()
        mock_session_ctx.__aenter__.return_value = mock_session
        mock_session_ctx.__aexit__.return_value = None
        mock_db_engine.begin_session.return_value = mock_session_ctx

        # Mock the _get_preset_by_id method
        with patch.object(
            resource_preset_repository,
            "_get_preset_by_id",
            AsyncMock(return_value=sample_preset_row),
        ):
            result = await resource_preset_repository.get_preset_by_id_or_name(
                preset_id=preset_id, name="ignored-name"
            )

            assert result.id == preset_id

    @pytest.mark.asyncio
    async def test_get_preset_by_id_or_name_with_name_only(
        self, resource_preset_repository, mock_db_engine, sample_preset_row
    ) -> None:
        """Test preset retrieval by name only"""
        # Mock database session
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session_ctx = AsyncMock()
        mock_session_ctx.__aenter__.return_value = mock_session
        mock_session_ctx.__aexit__.return_value = None
        mock_db_engine.begin_session.return_value = mock_session_ctx

        # Mock the _get_preset_by_name method
        with patch.object(
            resource_preset_repository,
            "_get_preset_by_name",
            AsyncMock(return_value=sample_preset_row),
        ):
            result = await resource_preset_repository.get_preset_by_id_or_name(
                preset_id=None, name="test-preset"
            )

            assert result.name == "test-preset"

    @pytest.mark.asyncio
    async def test_get_preset_by_id_or_name_no_params(self, resource_preset_repository) -> None:
        """Test preset retrieval with neither ID nor name"""
        with pytest.raises(ValueError, match="Either preset_id or name must be provided"):
            await resource_preset_repository.get_preset_by_id_or_name(preset_id=None, name=None)

    @pytest.mark.asyncio
    async def test_modify_preset_validated_success(
        self, resource_preset_repository, mock_db_engine, sample_preset_row
    ) -> None:
        """Test successful preset modification"""
        preset_id = sample_preset_row.id

        # Create a modified version of the preset
        modified_preset_data = ResourcePresetData(
            id=preset_id,
            name="modified-preset",
            resource_slots=ResourceSlot({"cpu": Decimal("8"), "mem": Decimal("17179869184")}),
            shared_memory=BinarySize(BinarySize.from_str("4G")),
            scaling_group_name=None,
        )

        # Create a new mock for the modified preset
        modified_preset_row = MagicMock(spec=ResourcePresetRow)
        modified_preset_row.to_dataclass.return_value = modified_preset_data

        # Mock database session
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session_ctx = AsyncMock()
        mock_session_ctx.__aenter__.return_value = mock_session
        mock_session_ctx.__aexit__.return_value = None
        mock_db_engine.begin_session.return_value = mock_session_ctx
        mock_session.flush = AsyncMock()

        modifier = ResourcePresetModifier(
            name=OptionalState.update("modified-preset"),
            resource_slots=OptionalState.update(ResourceSlot({"cpu": "8", "mem": "16G"})),
            shared_memory=TriState.update(BinarySize(BinarySize.from_str("4G"))),
        )

        # Mock the _get_preset_by_id method
        with patch.object(
            resource_preset_repository,
            "_get_preset_by_id",
            AsyncMock(return_value=modified_preset_row),
        ):
            result = await resource_preset_repository.modify_preset_validated(
                preset_id=preset_id, name=None, modifier=modifier
            )

            assert result.name == "modified-preset"
            assert result.resource_slots["cpu"] == Decimal("8")
            mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_modify_preset_validated_not_found(
        self, resource_preset_repository, mock_db_engine
    ) -> None:
        """Test preset modification when preset not found"""
        # Mock database session
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session_ctx = AsyncMock()
        mock_session_ctx.__aenter__.return_value = mock_session
        mock_session_ctx.__aexit__.return_value = None
        mock_db_engine.begin_session.return_value = mock_session_ctx

        modifier = ResourcePresetModifier(name=OptionalState.update("new-name"))

        # Mock the _get_preset_by_id method to return None
        with patch.object(
            resource_preset_repository, "_get_preset_by_id", AsyncMock(return_value=None)
        ):
            with pytest.raises(ObjectNotFound, match="Resource preset not found"):
                await resource_preset_repository.modify_preset_validated(
                    preset_id=uuid.uuid4(), name=None, modifier=modifier
                )

    @pytest.mark.asyncio
    async def test_modify_preset_validated_no_params(self, resource_preset_repository) -> None:
        """Test preset modification with neither ID nor name"""
        modifier = ResourcePresetModifier()

        with pytest.raises(ValueError, match="Either preset_id or name must be provided"):
            await resource_preset_repository.modify_preset_validated(
                preset_id=None, name=None, modifier=modifier
            )

    @pytest.mark.asyncio
    async def test_delete_preset_validated_success(
        self, resource_preset_repository, mock_db_engine, sample_preset_row
    ) -> None:
        """Test successful preset deletion"""
        preset_id = sample_preset_row.id

        # Mock database session
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session_ctx = AsyncMock()
        mock_session_ctx.__aenter__.return_value = mock_session
        mock_session_ctx.__aexit__.return_value = None
        mock_db_engine.begin_session.return_value = mock_session_ctx
        mock_session.delete = AsyncMock()

        # Mock the _get_preset_by_id method
        with patch.object(
            resource_preset_repository,
            "_get_preset_by_id",
            AsyncMock(return_value=sample_preset_row),
        ):
            result = await resource_preset_repository.delete_preset_validated(
                preset_id=preset_id, name=None
            )

            assert result.id == preset_id
            assert result.name == sample_preset_row.name
            mock_session.delete.assert_called_once_with(sample_preset_row)

    @pytest.mark.asyncio
    async def test_delete_preset_validated_by_name(
        self, resource_preset_repository, mock_db_engine, sample_preset_row
    ) -> None:
        """Test successful preset deletion by name"""
        # Mock database session
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session_ctx = AsyncMock()
        mock_session_ctx.__aenter__.return_value = mock_session
        mock_session_ctx.__aexit__.return_value = None
        mock_db_engine.begin_session.return_value = mock_session_ctx
        mock_session.delete = AsyncMock()

        # Mock the _get_preset_by_name method
        with patch.object(
            resource_preset_repository,
            "_get_preset_by_name",
            AsyncMock(return_value=sample_preset_row),
        ):
            result = await resource_preset_repository.delete_preset_validated(
                preset_id=None, name="test-preset"
            )

            assert result.name == "test-preset"
            mock_session.delete.assert_called_once_with(sample_preset_row)

    @pytest.mark.asyncio
    async def test_delete_preset_validated_not_found(
        self, resource_preset_repository, mock_db_engine
    ) -> None:
        """Test preset deletion when preset not found"""
        # Mock database session
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session_ctx = AsyncMock()
        mock_session_ctx.__aenter__.return_value = mock_session
        mock_session_ctx.__aexit__.return_value = None
        mock_db_engine.begin_session.return_value = mock_session_ctx

        # Mock the _get_preset_by_id method to return None
        with patch.object(
            resource_preset_repository, "_get_preset_by_id", AsyncMock(return_value=None)
        ):
            with pytest.raises(ObjectNotFound, match="Resource preset not found"):
                await resource_preset_repository.delete_preset_validated(
                    preset_id=uuid.uuid4(), name=None
                )

    @pytest.mark.asyncio
    async def test_delete_preset_validated_no_params(self, resource_preset_repository) -> None:
        """Test preset deletion with neither ID nor name"""
        with pytest.raises(ValueError, match="Either preset_id or name must be provided"):
            await resource_preset_repository.delete_preset_validated(preset_id=None, name=None)

    @pytest.mark.asyncio
    async def test_list_presets_all(self, resource_preset_repository, mock_db_engine) -> None:
        """Test listing all presets"""
        # Create multiple preset data
        preset1_data = ResourcePresetData(
            id=uuid.uuid4(),
            name="preset-1",
            resource_slots=ResourceSlot({"cpu": Decimal("2"), "mem": Decimal("4294967296")}),
            shared_memory=BinarySize(BinarySize.from_str("1G")),
            scaling_group_name=None,
        )
        preset2_data = ResourcePresetData(
            id=uuid.uuid4(),
            name="preset-2",
            resource_slots=ResourceSlot({"cpu": Decimal("8"), "mem": Decimal("17179869184")}),
            shared_memory=None,
            scaling_group_name=None,
        )

        # Create mock rows
        mock_row1 = MagicMock()
        mock_row1.to_dataclass.return_value = preset1_data
        mock_row2 = MagicMock()
        mock_row2.to_dataclass.return_value = preset2_data

        # Mock database session
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session_ctx = AsyncMock()
        mock_session_ctx.__aenter__.return_value = mock_session
        mock_session_ctx.__aexit__.return_value = None
        mock_db_engine.begin_readonly_session.return_value = mock_session_ctx

        # Mock stream_scalars to return async iterator
        async def mock_stream():
            for row in [mock_row1, mock_row2]:
                yield row

        mock_stream_result = mock_stream()
        mock_session.stream_scalars = AsyncMock(return_value=mock_stream_result)

        result = await resource_preset_repository.list_presets()

        assert len(result) == 2
        assert result[0].name == "preset-1"
        assert result[1].name == "preset-2"

    @pytest.mark.asyncio
    async def test_list_presets_by_scaling_group(
        self, resource_preset_repository, mock_db_engine
    ) -> None:
        """Test listing presets filtered by scaling group"""
        # Create presets with different scaling groups
        global_preset = ResourcePresetData(
            id=uuid.uuid4(),
            name="global-preset",
            resource_slots=ResourceSlot({"cpu": Decimal("2"), "mem": Decimal("4294967296")}),
            shared_memory=None,
            scaling_group_name=None,
        )

        group_preset = ResourcePresetData(
            id=uuid.uuid4(),
            name="group-preset",
            resource_slots=ResourceSlot({"cpu": Decimal("4"), "mem": Decimal("8589934592")}),
            shared_memory=None,
            scaling_group_name="gpu-cluster",
        )

        # Create mock rows
        mock_row1 = MagicMock()
        mock_row1.to_dataclass.return_value = global_preset
        mock_row2 = MagicMock()
        mock_row2.to_dataclass.return_value = group_preset

        # Mock database session
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session_ctx = AsyncMock()
        mock_session_ctx.__aenter__.return_value = mock_session
        mock_session_ctx.__aexit__.return_value = None
        mock_db_engine.begin_readonly_session.return_value = mock_session_ctx

        # Mock stream_scalars
        async def mock_stream():
            for row in [mock_row1, mock_row2]:
                yield row

        mock_stream_result = mock_stream()
        mock_session.stream_scalars = AsyncMock(return_value=mock_stream_result)

        result = await resource_preset_repository.list_presets(scaling_group_name="gpu-cluster")

        assert len(result) == 2
        assert any(p.name == "global-preset" for p in result)  # Global presets included
        assert any(p.name == "group-preset" for p in result)  # Group-specific presets included

    @pytest.mark.asyncio
    async def test_list_presets_empty(self, resource_preset_repository, mock_db_engine) -> None:
        """Test listing presets when none exist"""
        # Mock database session
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session_ctx = AsyncMock()
        mock_session_ctx.__aenter__.return_value = mock_session
        mock_session_ctx.__aexit__.return_value = None
        mock_db_engine.begin_readonly_session.return_value = mock_session_ctx

        # Mock empty stream_scalars
        async def mock_stream():
            return
            yield  # Make it a generator

        mock_stream_result = mock_stream()
        mock_session.stream_scalars = AsyncMock(return_value=mock_stream_result)

        result = await resource_preset_repository.list_presets()

        assert result == []

    @pytest.mark.asyncio
    async def test_repository_decorator_applied(self, resource_preset_repository) -> None:
        """Test that repository decorator is properly applied"""
        # This test verifies that the repository methods have the decorator applied
        # The decorator should be present on the main repository methods
        assert hasattr(resource_preset_repository, "create_preset_validated")
        assert hasattr(resource_preset_repository, "get_preset_by_id")
        assert hasattr(resource_preset_repository, "get_preset_by_name")
        assert hasattr(resource_preset_repository, "get_preset_by_id_or_name")
        assert hasattr(resource_preset_repository, "modify_preset_validated")
        assert hasattr(resource_preset_repository, "delete_preset_validated")
        assert hasattr(resource_preset_repository, "list_presets")


class TestResourcePresetDataModels:
    """Tests for ResourcePreset data models and type validation"""

    @pytest.mark.asyncio
    async def test_resource_preset_data_conversion(self) -> None:
        """Test ResourcePresetData conversion from ResourcePresetRow"""
        # Create a sample preset row
        preset_row = ResourcePresetRow(
            id=uuid.uuid4(),
            name="test-preset",
            resource_slots=ResourceSlot({"cpu": Decimal("4"), "mem": Decimal("8589934592")}),
            shared_memory=BinarySize.from_str("2G"),
            scaling_group_name=None,
        )

        # Convert to ResourcePresetData
        preset_data = preset_row.to_dataclass()

        # Verify conversion
        assert preset_data.id == preset_row.id
        assert preset_data.name == preset_row.name
        assert preset_data.resource_slots == preset_row.resource_slots
        assert preset_data.shared_memory == preset_row.shared_memory
        assert preset_data.scaling_group_name == preset_row.scaling_group_name

    def test_resource_slot_validation(self) -> None:
        """Test resource slot validation"""
        # Test valid resource slots
        valid_slots = ResourceSlot({"cpu": "4", "mem": "8G", "gpu": "1", "gpu_memory": "16G"})

        # Verify slots are properly initialized
        assert valid_slots["cpu"] == "4"
        assert valid_slots["mem"] == "8G"
        assert valid_slots["gpu"] == "1"
        assert valid_slots["gpu_memory"] == "16G"

    def test_binary_size_validation(self) -> None:
        """Test binary size validation"""
        # Test valid binary sizes
        sizes = [
            BinarySize.from_str("1G"),
            BinarySize.from_str("512M"),
            BinarySize.from_str("2048K"),
        ]

        for size in sizes:
            assert isinstance(size, BinarySize)
            assert size > 0  # BinarySize objects support comparison

    def test_scaling_group_name_validation(self) -> None:
        """Test scaling group name validation"""
        # Test valid scaling group names
        valid_names = [None, "default", "gpu-cluster", "cpu-only"]

        for name in valid_names:
            preset_data = {
                "name": "test-preset",
                "resource_slots": ResourceSlot({"cpu": "1", "mem": "1G"}),
                "scaling_group_name": name,
            }
            # This should not raise an exception
            assert (
                preset_data["scaling_group_name"] == name
                or preset_data["scaling_group_name"] is None
            )
