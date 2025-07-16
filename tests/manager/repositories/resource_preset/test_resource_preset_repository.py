import uuid
from typing import Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import sqlalchemy as sa
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


@pytest.fixture
def mock_db_engine():
    """Mock database engine fixture"""
    mock_engine = MagicMock(spec=ExtendedAsyncSAEngine)
    
    # Create a mock session context manager
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session_ctx = AsyncMock()
    mock_session_ctx.__aenter__.return_value = mock_session
    mock_session_ctx.__aexit__.return_value = None
    
    # Configure the mock engine
    mock_engine.begin_session.return_value = mock_session_ctx
    mock_engine.begin_readonly_session.return_value = mock_session_ctx
    
    return mock_engine, mock_session


@pytest.fixture
def repository(mock_db_engine):
    """Create repository instance with mocked database"""
    engine, _ = mock_db_engine
    return ResourcePresetRepository(db=engine)


@pytest.fixture
def sample_preset_data():
    """Sample resource preset data for testing"""
    return ResourcePresetData(
        id=uuid.uuid4(),
        name="test-preset",
        resource_slots=ResourceSlot({"cpu": "4", "memory": "8G"}),
        shared_memory=BinarySize.from_str("2G"),
        scaling_group_name=None,
    )


@pytest.fixture
def sample_preset_row(sample_preset_data):
    """Mock ResourcePresetRow instance"""
    mock_row = MagicMock(spec=ResourcePresetRow)
    mock_row.id = sample_preset_data.id
    mock_row.name = sample_preset_data.name
    mock_row.resource_slots = sample_preset_data.resource_slots
    mock_row.shared_memory = sample_preset_data.shared_memory
    mock_row.scaling_group_name = sample_preset_data.scaling_group_name
    mock_row.to_dataclass.return_value = sample_preset_data
    return mock_row


class TestResourcePresetRepository:
    """Test cases for ResourcePresetRepository"""

    @pytest.mark.asyncio
    async def test_create_preset_validated_success(
        self, repository, mock_db_engine, sample_preset_data, sample_preset_row
    ):
        """Test successful preset creation"""
        _, mock_session = mock_db_engine
        
        creator = ResourcePresetCreator(
            name="new-preset",
            resource_slots=ResourceSlot({"cpu": "2", "memory": "4G"}),
            shared_memory=BinarySize.from_str("1G"),
            scaling_group_name=None,
        )
        
        # Mock ResourcePresetRow.create to return the preset row
        with patch.object(
            ResourcePresetRow, 'create', AsyncMock(return_value=sample_preset_row)
        ) as mock_create:
            result = await repository.create_preset_validated(creator)
        
        assert result is not None
        assert result.id == sample_preset_data.id
        assert result.name == sample_preset_data.name
        mock_create.assert_called_once_with(creator, db_session=mock_session)

    @pytest.mark.asyncio
    async def test_create_preset_validated_duplicate(
        self, repository, mock_db_engine
    ):
        """Test preset creation with duplicate name"""
        _, mock_session = mock_db_engine
        
        creator = ResourcePresetCreator(
            name="duplicate-preset",
            resource_slots=ResourceSlot({"cpu": "2", "memory": "4G"}),
            shared_memory=None,
            scaling_group_name=None,
        )
        
        # Mock ResourcePresetRow.create to return None (duplicate)
        with patch.object(
            ResourcePresetRow, 'create', AsyncMock(return_value=None)
        ):
            result = await repository.create_preset_validated(creator)
        
        assert result is None

    @pytest.mark.asyncio
    async def test_get_preset_by_id_success(
        self, repository, mock_db_engine, sample_preset_data, sample_preset_row
    ):
        """Test successful preset retrieval by ID"""
        _, mock_session = mock_db_engine
        preset_id = sample_preset_data.id
        
        # Mock session.scalar to return the preset row
        mock_session.scalar = AsyncMock(return_value=sample_preset_row)
        
        result = await repository.get_preset_by_id(preset_id)
        
        assert result.id == preset_id
        assert result.name == sample_preset_data.name
        mock_session.scalar.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_preset_by_id_not_found(
        self, repository, mock_db_engine
    ):
        """Test preset retrieval by ID when not found"""
        _, mock_session = mock_db_engine
        preset_id = uuid.uuid4()
        
        # Mock session.scalar to return None
        mock_session.scalar = AsyncMock(return_value=None)
        
        with pytest.raises(ObjectNotFound, match="Resource preset not found"):
            await repository.get_preset_by_id(preset_id)

    @pytest.mark.asyncio
    async def test_get_preset_by_name_success(
        self, repository, mock_db_engine, sample_preset_data, sample_preset_row
    ):
        """Test successful preset retrieval by name"""
        _, mock_session = mock_db_engine
        
        # Mock session.scalar to return the preset row
        mock_session.scalar = AsyncMock(return_value=sample_preset_row)
        
        result = await repository.get_preset_by_name("test-preset")
        
        assert result.name == "test-preset"
        assert result.id == sample_preset_data.id
        mock_session.scalar.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_preset_by_name_not_found(
        self, repository, mock_db_engine
    ):
        """Test preset retrieval by name when not found"""
        _, mock_session = mock_db_engine
        
        # Mock session.scalar to return None
        mock_session.scalar = AsyncMock(return_value=None)
        
        with pytest.raises(ObjectNotFound, match="Resource preset not found"):
            await repository.get_preset_by_name("non-existent")

    @pytest.mark.asyncio
    async def test_get_preset_by_id_or_name_with_id(
        self, repository, mock_db_engine, sample_preset_data, sample_preset_row
    ):
        """Test preset retrieval by ID when both ID and name provided"""
        _, mock_session = mock_db_engine
        preset_id = sample_preset_data.id
        
        # Mock session.scalar to return the preset row
        mock_session.scalar = AsyncMock(return_value=sample_preset_row)
        
        result = await repository.get_preset_by_id_or_name(
            preset_id=preset_id, name="ignored-name"
        )
        
        assert result.id == preset_id
        # Should have called scalar only once (for ID lookup)
        mock_session.scalar.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_preset_by_id_or_name_with_name_only(
        self, repository, mock_db_engine, sample_preset_data, sample_preset_row
    ):
        """Test preset retrieval by name only"""
        _, mock_session = mock_db_engine
        
        # Mock session.scalar to return the preset row
        mock_session.scalar = AsyncMock(return_value=sample_preset_row)
        
        result = await repository.get_preset_by_id_or_name(
            preset_id=None, name="test-preset"
        )
        
        assert result.name == "test-preset"
        mock_session.scalar.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_preset_by_id_or_name_no_params(
        self, repository
    ):
        """Test preset retrieval with neither ID nor name"""
        with pytest.raises(ValueError, match="Either preset_id or name must be provided"):
            await repository.get_preset_by_id_or_name(preset_id=None, name=None)

    @pytest.mark.asyncio
    async def test_modify_preset_validated_by_id(
        self, repository, mock_db_engine, sample_preset_data, sample_preset_row
    ):
        """Test successful preset modification by ID"""
        _, mock_session = mock_db_engine
        preset_id = sample_preset_data.id
        
        # Create a modified version of the preset
        modified_preset_data = ResourcePresetData(
            id=preset_id,
            name="modified-preset",
            resource_slots=ResourceSlot({"cpu": "8", "memory": "16G"}),
            shared_memory=BinarySize.from_str("4G"),
            scaling_group_name=None,
        )
        
        # Mock the modified preset row
        mock_preset_row = MagicMock(spec=ResourcePresetRow)
        mock_preset_row.to_dataclass.return_value = modified_preset_data
        
        # Mock session.scalar to return the preset row
        mock_session.scalar = AsyncMock(return_value=mock_preset_row)
        mock_session.flush = AsyncMock()
        
        modifier = ResourcePresetModifier(
            name=OptionalState.update("modified-preset"),
            resource_slots=OptionalState.update(ResourceSlot({"cpu": "8", "memory": "16G"})),
            shared_memory=TriState.update(BinarySize.from_str("4G")),
        )
        
        result = await repository.modify_preset_validated(
            preset_id=preset_id, name=None, modifier=modifier
        )
        
        assert result.name == "modified-preset"
        assert result.resource_slots["cpu"] == "8"
        mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_modify_preset_validated_not_found(
        self, repository, mock_db_engine
    ):
        """Test preset modification when preset not found"""
        _, mock_session = mock_db_engine
        
        # Mock session.scalar to return None
        mock_session.scalar = AsyncMock(return_value=None)
        
        modifier = ResourcePresetModifier(
            name=OptionalState.update("new-name")
        )
        
        with pytest.raises(ObjectNotFound, match="Resource preset not found"):
            await repository.modify_preset_validated(
                preset_id=uuid.uuid4(), name=None, modifier=modifier
            )

    @pytest.mark.asyncio
    async def test_modify_preset_validated_no_params(
        self, repository
    ):
        """Test preset modification with neither ID nor name"""
        modifier = ResourcePresetModifier()
        
        with pytest.raises(ValueError, match="Either preset_id or name must be provided"):
            await repository.modify_preset_validated(
                preset_id=None, name=None, modifier=modifier
            )

    @pytest.mark.asyncio
    async def test_delete_preset_validated_by_id(
        self, repository, mock_db_engine, sample_preset_data, sample_preset_row
    ):
        """Test successful preset deletion by ID"""
        _, mock_session = mock_db_engine
        preset_id = sample_preset_data.id
        
        # Mock session.scalar to return the preset row
        mock_session.scalar = AsyncMock(return_value=sample_preset_row)
        mock_session.delete = AsyncMock()
        
        result = await repository.delete_preset_validated(
            preset_id=preset_id, name=None
        )
        
        assert result.id == preset_id
        assert result.name == sample_preset_data.name
        mock_session.delete.assert_called_once_with(sample_preset_row)

    @pytest.mark.asyncio
    async def test_delete_preset_validated_by_name(
        self, repository, mock_db_engine, sample_preset_data, sample_preset_row
    ):
        """Test successful preset deletion by name"""
        _, mock_session = mock_db_engine
        
        # Mock session.scalar to return the preset row
        mock_session.scalar = AsyncMock(return_value=sample_preset_row)
        mock_session.delete = AsyncMock()
        
        result = await repository.delete_preset_validated(
            preset_id=None, name="test-preset"
        )
        
        assert result.name == "test-preset"
        mock_session.delete.assert_called_once_with(sample_preset_row)

    @pytest.mark.asyncio
    async def test_delete_preset_validated_not_found(
        self, repository, mock_db_engine
    ):
        """Test preset deletion when preset not found"""
        _, mock_session = mock_db_engine
        
        # Mock session.scalar to return None
        mock_session.scalar = AsyncMock(return_value=None)
        
        with pytest.raises(ObjectNotFound, match="Resource preset not found"):
            await repository.delete_preset_validated(
                preset_id=uuid.uuid4(), name=None
            )

    @pytest.mark.asyncio
    async def test_delete_preset_validated_no_params(
        self, repository
    ):
        """Test preset deletion with neither ID nor name"""
        with pytest.raises(ValueError, match="Either preset_id or name must be provided"):
            await repository.delete_preset_validated(preset_id=None, name=None)

    @pytest.mark.asyncio
    async def test_list_presets_all(
        self, repository, mock_db_engine, sample_preset_data
    ):
        """Test listing all presets"""
        _, mock_session = mock_db_engine
        
        # Create multiple preset rows
        preset1_data = sample_preset_data
        preset2_data = ResourcePresetData(
            id=uuid.uuid4(),
            name="preset-2",
            resource_slots=ResourceSlot({"cpu": "8", "memory": "16G"}),
            shared_memory=None,
            scaling_group_name=None,
        )
        
        mock_row1 = MagicMock()
        mock_row1.to_dataclass.return_value = preset1_data
        mock_row2 = MagicMock()
        mock_row2.to_dataclass.return_value = preset2_data
        
        # Mock stream_scalars to return async iterator
        async def mock_stream():
            for row in [mock_row1, mock_row2]:
                yield row
        
        mock_stream_result = mock_stream()
        mock_session.stream_scalars = AsyncMock(return_value=mock_stream_result)
        
        result = await repository.list_presets()
        
        assert len(result) == 2
        assert result[0].name == "test-preset"
        assert result[1].name == "preset-2"

    @pytest.mark.asyncio
    async def test_list_presets_by_scaling_group(
        self, repository, mock_db_engine
    ):
        """Test listing presets filtered by scaling group"""
        _, mock_session = mock_db_engine
        
        # Create presets with different scaling groups
        global_preset = ResourcePresetData(
            id=uuid.uuid4(),
            name="global-preset",
            resource_slots=ResourceSlot({"cpu": "2", "memory": "4G"}),
            shared_memory=None,
            scaling_group_name=None,
        )
        
        group_preset = ResourcePresetData(
            id=uuid.uuid4(),
            name="group-preset",
            resource_slots=ResourceSlot({"cpu": "4", "memory": "8G"}),
            shared_memory=None,
            scaling_group_name="gpu-cluster",
        )
        
        mock_row1 = MagicMock()
        mock_row1.to_dataclass.return_value = global_preset
        mock_row2 = MagicMock()
        mock_row2.to_dataclass.return_value = group_preset
        
        # Mock stream_scalars
        async def mock_stream():
            for row in [mock_row1, mock_row2]:
                yield row
        
        mock_stream_result = mock_stream()
        mock_session.stream_scalars = AsyncMock(return_value=mock_stream_result)
        
        result = await repository.list_presets(scaling_group_name="gpu-cluster")
        
        assert len(result) == 2
        assert any(p.name == "global-preset" for p in result)  # Global presets included
        assert any(p.name == "group-preset" for p in result)   # Group-specific presets included

    @pytest.mark.asyncio
    async def test_list_presets_empty(
        self, repository, mock_db_engine
    ):
        """Test listing presets when none exist"""
        _, mock_session = mock_db_engine
        
        # Mock empty stream_scalars
        async def mock_stream():
            return
            yield  # Make it a generator
        
        mock_stream_result = mock_stream()
        mock_session.stream_scalars = AsyncMock(return_value=mock_stream_result)
        
        result = await repository.list_presets()
        
        assert result == []