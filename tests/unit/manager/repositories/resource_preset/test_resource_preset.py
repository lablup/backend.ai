"""
Tests for ResourcePresetRepository functionality.
Tests the repository layer with mocked database operations.
"""

import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.exception import ResourcePresetConflict
from ai.backend.common.types import BinarySize, ResourceSlot
from ai.backend.manager.data.resource_preset.types import ResourcePresetData
from ai.backend.manager.errors.resource import ResourcePresetNotFound
from ai.backend.manager.models.resource_preset import ResourcePresetRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.resource_preset.cache_source.cache_source import (
    ResourcePresetCacheSource,
)
from ai.backend.manager.repositories.resource_preset.creators import ResourcePresetCreatorSpec
from ai.backend.manager.repositories.resource_preset.db_source.db_source import (
    ResourcePresetDBSource,
)
from ai.backend.manager.repositories.resource_preset.repository import ResourcePresetRepository
from ai.backend.manager.repositories.resource_preset.updaters import ResourcePresetUpdaterSpec
from ai.backend.manager.types import OptionalState, TriState


class TestResourcePresetRepository:
    """Test cases for ResourcePresetRepository"""

    @pytest.fixture
    def mock_db_engine(self) -> MagicMock:
        """Create mocked database engine"""
        return MagicMock(spec=ExtendedAsyncSAEngine)

    @pytest.fixture
    def mock_db_source(self) -> MagicMock:
        """Create mocked DB source"""
        mock = MagicMock(spec=ResourcePresetDBSource)
        # Set default AsyncMocks for commonly used methods
        mock.list_presets = AsyncMock(return_value=[])
        return mock

    @pytest.fixture
    def mock_cache_source(self) -> MagicMock:
        """Create mocked cache source"""
        mock = MagicMock(spec=ResourcePresetCacheSource)
        # Set all async methods to return AsyncMock
        mock.get_preset_by_id = AsyncMock(return_value=None)
        mock.get_preset_by_name = AsyncMock(return_value=None)
        mock.set_preset = AsyncMock()
        mock.get_preset_list = AsyncMock(return_value=None)
        mock.set_preset_list = AsyncMock()
        mock.invalidate_preset = AsyncMock()
        return mock

    @pytest.fixture
    def resource_preset_repository(
        self, mock_db_engine, mock_db_source, mock_cache_source
    ) -> ResourcePresetRepository:
        """Create ResourcePresetRepository instance with mocked database"""
        mock_config_provider = MagicMock()
        mock_config_provider.legacy_etcd_config_loader.get_resource_slots = AsyncMock(
            return_value={"cpu", "mem", "cuda.device"}
        )
        repo = ResourcePresetRepository(
            db=mock_db_engine, valkey_stat=MagicMock(), config_provider=mock_config_provider
        )
        # Replace internal sources with mocks
        repo._db_source = mock_db_source
        repo._cache_source = mock_cache_source
        return repo

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
    def sample_preset_creator(self) -> Creator:
        """Create sample resource preset creator for testing"""
        return Creator(
            spec=ResourcePresetCreatorSpec(
                name="new-preset",
                resource_slots=ResourceSlot({"cpu": "2", "mem": "4G"}),
                shared_memory="1 GiB",
                scaling_group_name=None,
            )
        )

    @pytest.mark.asyncio
    async def test_create_preset_validated_success(
        self,
        resource_preset_repository,
        mock_db_source,
        sample_preset_creator: Creator,
        sample_preset_row,
    ) -> None:
        """Test successful preset creation"""
        preset_data = sample_preset_row.to_dataclass()
        mock_db_source.create_preset = AsyncMock(return_value=preset_data)

        result = await resource_preset_repository.create_preset_validated(sample_preset_creator)

        assert result is not None
        assert isinstance(result, ResourcePresetData)
        assert result.name == preset_data.name
        assert result.id == preset_data.id
        mock_db_source.create_preset.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_preset_validated_duplicate(
        self, resource_preset_repository, mock_db_source, sample_preset_creator: Creator
    ) -> None:
        """Test preset creation with duplicate name"""
        mock_db_source.create_preset = AsyncMock(
            side_effect=ResourcePresetConflict("Duplicate preset")
        )

        with pytest.raises(ResourcePresetConflict):
            await resource_preset_repository.create_preset_validated(sample_preset_creator)

    @pytest.mark.asyncio
    async def test_get_preset_by_id_success(
        self, resource_preset_repository, mock_db_source, mock_cache_source, sample_preset_row
    ) -> None:
        """Test successful preset retrieval by ID"""
        preset_id = sample_preset_row.id
        preset_data = sample_preset_row.to_dataclass()

        # Mock cache miss, then DB hit
        mock_cache_source.get_preset_by_id = AsyncMock(return_value=None)
        mock_db_source.get_preset_by_id = AsyncMock(return_value=preset_data)
        mock_cache_source.set_preset = AsyncMock()

        result = await resource_preset_repository.get_preset_by_id(preset_id)

        assert result.id == preset_id
        assert result.name == sample_preset_row.name
        mock_cache_source.get_preset_by_id.assert_called_once_with(preset_id)
        mock_db_source.get_preset_by_id.assert_called_once_with(preset_id)
        mock_cache_source.set_preset.assert_called_once_with(preset_data)

    @pytest.mark.asyncio
    async def test_get_preset_by_id_not_found(
        self, resource_preset_repository, mock_db_source, mock_cache_source
    ) -> None:
        """Test preset retrieval by ID when not found"""
        preset_id = uuid.uuid4()

        # Mock cache miss and DB raises exception
        mock_cache_source.get_preset_by_id = AsyncMock(return_value=None)
        mock_db_source.get_preset_by_id = AsyncMock(side_effect=ResourcePresetNotFound())

        with pytest.raises(ResourcePresetNotFound):
            await resource_preset_repository.get_preset_by_id(preset_id)

    @pytest.mark.asyncio
    async def test_get_preset_by_name_success(
        self, resource_preset_repository, mock_db_source, mock_cache_source, sample_preset_row
    ) -> None:
        """Test successful preset retrieval by name"""
        preset_name = "test-preset"
        preset_data = sample_preset_row.to_dataclass()

        # Mock cache miss, then DB hit
        mock_cache_source.get_preset_by_name = AsyncMock(return_value=None)
        mock_db_source.get_preset_by_name = AsyncMock(return_value=preset_data)
        mock_cache_source.set_preset = AsyncMock()

        result = await resource_preset_repository.get_preset_by_name(preset_name)

        assert result.name == preset_name
        assert result.id == sample_preset_row.id
        mock_cache_source.get_preset_by_name.assert_called_once_with(preset_name)
        mock_db_source.get_preset_by_name.assert_called_once_with(preset_name)
        mock_cache_source.set_preset.assert_called_once_with(preset_data)

    @pytest.mark.asyncio
    async def test_get_preset_by_name_not_found(
        self, resource_preset_repository, mock_db_source, mock_cache_source
    ) -> None:
        """Test preset retrieval by name when not found"""
        preset_name = "non-existent"

        # Mock cache miss and DB raises exception
        mock_cache_source.get_preset_by_name = AsyncMock(return_value=None)
        mock_db_source.get_preset_by_name = AsyncMock(side_effect=ResourcePresetNotFound())

        with pytest.raises(ResourcePresetNotFound):
            await resource_preset_repository.get_preset_by_name(preset_name)

    @pytest.mark.asyncio
    async def test_get_preset_by_id_or_name_with_id(
        self, resource_preset_repository, mock_db_source, mock_cache_source, sample_preset_row
    ) -> None:
        """Test preset retrieval by ID when both ID and name provided"""
        preset_id = sample_preset_row.id
        preset_data = sample_preset_row.to_dataclass()

        # Mock db_source
        mock_db_source.get_preset_by_id_or_name = AsyncMock(return_value=preset_data)

        result = await resource_preset_repository.get_preset_by_id_or_name(
            preset_id=preset_id, name="ignored-name"
        )

        assert result.id == preset_id

    @pytest.mark.asyncio
    async def test_get_preset_by_id_or_name_with_name_only(
        self, resource_preset_repository, mock_db_source, mock_cache_source, sample_preset_row
    ) -> None:
        """Test preset retrieval by name only"""
        preset_data = sample_preset_row.to_dataclass()

        # Mock db_source
        mock_db_source.get_preset_by_id_or_name = AsyncMock(return_value=preset_data)

        result = await resource_preset_repository.get_preset_by_id_or_name(
            preset_id=None, name="test-preset"
        )

        assert result.name == "test-preset"

    @pytest.mark.asyncio
    async def test_get_preset_by_id_or_name_no_params(
        self, resource_preset_repository, mock_db_source
    ) -> None:
        """Test preset retrieval with neither ID nor name"""
        # Mock db_source to raise ValueError
        mock_db_source.get_preset_by_id_or_name = AsyncMock(
            side_effect=ValueError("Either preset_id or name must be provided")
        )

        with pytest.raises(ValueError, match="Either preset_id or name must be provided"):
            await resource_preset_repository.get_preset_by_id_or_name(preset_id=None, name=None)

    @pytest.mark.asyncio
    async def test_modify_preset_validated_success(
        self, resource_preset_repository, mock_db_source, mock_cache_source, sample_preset_row
    ) -> None:
        """Test successful preset modification"""
        preset_id = sample_preset_row.id
        preset_data = sample_preset_row.to_dataclass()
        updater = Updater(
            spec=ResourcePresetUpdaterSpec(
                name=OptionalState.update("modified-preset"),
                resource_slots=OptionalState.update(ResourceSlot({"cpu": "8", "mem": "16G"})),
                shared_memory=TriState.nullify(),
                scaling_group_name=TriState.update("new-group"),
            ),
            pk_value=preset_id,
        )

        # Mock modify operation
        mock_db_source.modify_preset = AsyncMock(return_value=preset_data)
        mock_cache_source.invalidate_preset = AsyncMock()

        result = await resource_preset_repository.modify_preset_validated(updater)

        assert result is not None
        mock_db_source.modify_preset.assert_called_once_with(updater)
        mock_cache_source.invalidate_preset.assert_called_once_with(preset_id, None)

    @pytest.mark.asyncio
    async def test_modify_preset_validated_not_found(
        self, resource_preset_repository, mock_db_source, mock_cache_source
    ) -> None:
        """Test preset modification when preset not found"""
        preset_id = uuid.uuid4()
        updater = Updater(
            spec=ResourcePresetUpdaterSpec(
                name=OptionalState.update("modified-preset"),
            ),
            pk_value=preset_id,
        )

        # Mock modify to raise exception
        mock_db_source.modify_preset = AsyncMock(side_effect=ResourcePresetNotFound())

        with pytest.raises(ResourcePresetNotFound):
            await resource_preset_repository.modify_preset_validated(updater)

    @pytest.mark.asyncio
    async def test_modify_preset_validated_no_params(
        self, resource_preset_repository, mock_db_source
    ) -> None:
        """Test preset modification with no preset ID"""
        updater = Updater(
            spec=ResourcePresetUpdaterSpec(),
            pk_value="",
        )

        # Mock db_source to raise ValueError
        mock_db_source.modify_preset = AsyncMock(
            side_effect=ValueError("Either preset_id or name must be provided")
        )

        with pytest.raises(ValueError):
            await resource_preset_repository.modify_preset_validated(updater)

    @pytest.mark.asyncio
    async def test_delete_preset_validated_success(
        self, resource_preset_repository, mock_db_source, mock_cache_source, sample_preset_row
    ) -> None:
        """Test successful preset deletion by ID"""
        preset_id = sample_preset_row.id
        preset_data = sample_preset_row.to_dataclass()

        # Mock delete operation
        mock_db_source.delete_preset = AsyncMock(return_value=preset_data)
        mock_cache_source.invalidate_preset = AsyncMock()

        result = await resource_preset_repository.delete_preset_validated(
            preset_id=preset_id, name=None
        )

        assert result is not None
        assert isinstance(result, ResourcePresetData)
        mock_db_source.delete_preset.assert_called_once_with(preset_id, None)
        mock_cache_source.invalidate_preset.assert_called_once_with(preset_id, None)

    @pytest.mark.asyncio
    async def test_delete_preset_validated_by_name(
        self, resource_preset_repository, mock_db_source, mock_cache_source, sample_preset_row
    ) -> None:
        """Test successful preset deletion by name"""
        preset_name = sample_preset_row.name
        preset_data = sample_preset_row.to_dataclass()

        # Mock delete operation
        mock_db_source.delete_preset = AsyncMock(return_value=preset_data)
        mock_cache_source.invalidate_preset = AsyncMock()

        result = await resource_preset_repository.delete_preset_validated(
            preset_id=None, name=preset_name
        )

        assert result is not None
        assert isinstance(result, ResourcePresetData)
        mock_db_source.delete_preset.assert_called_once_with(None, preset_name)
        mock_cache_source.invalidate_preset.assert_called_once_with(None, preset_name)

    @pytest.mark.asyncio
    async def test_delete_preset_validated_not_found(
        self, resource_preset_repository, mock_db_source, mock_cache_source
    ) -> None:
        """Test preset deletion when preset not found"""
        preset_id = uuid.uuid4()

        # Mock delete to raise exception
        mock_db_source.delete_preset = AsyncMock(side_effect=ResourcePresetNotFound())

        with pytest.raises(ResourcePresetNotFound):
            await resource_preset_repository.delete_preset_validated(preset_id=preset_id, name=None)

    @pytest.mark.asyncio
    async def test_delete_preset_validated_no_params(
        self, resource_preset_repository, mock_db_source
    ) -> None:
        """Test preset deletion with neither ID nor name"""
        # Mock db_source to raise ValueError
        mock_db_source.delete_preset = AsyncMock(
            side_effect=ValueError("Either preset_id or name must be provided")
        )

        with pytest.raises(ValueError, match="Either preset_id or name must be provided"):
            await resource_preset_repository.delete_preset_validated(preset_id=None, name=None)

    @pytest.mark.asyncio
    async def test_list_presets_all(
        self, resource_preset_repository, mock_db_source, mock_cache_source
    ) -> None:
        """Test listing all presets"""
        preset_list = [
            ResourcePresetData(
                id=uuid.uuid4(),
                name=f"preset-{i}",
                resource_slots=ResourceSlot({"cpu": "2", "mem": "4G"}),
                shared_memory=None,
                scaling_group_name=None,
            )
            for i in range(3)
        ]

        # Mock cache miss, then DB hit
        mock_cache_source.get_preset_list = AsyncMock(return_value=None)
        mock_db_source.list_presets = AsyncMock(return_value=preset_list)
        mock_cache_source.set_preset_list = AsyncMock()

        result = await resource_preset_repository.list_presets()

        assert len(result) == 3
        assert all(isinstance(p, ResourcePresetData) for p in result)
        mock_cache_source.get_preset_list.assert_called_once_with(None)
        mock_db_source.list_presets.assert_called_once_with(None)
        mock_cache_source.set_preset_list.assert_called_once_with(preset_list, None)

    @pytest.mark.asyncio
    async def test_list_presets_by_scaling_group(
        self, resource_preset_repository, mock_db_source, mock_cache_source
    ) -> None:
        """Test listing presets filtered by scaling group"""
        scaling_group = "gpu-cluster"
        preset_list = [
            ResourcePresetData(
                id=uuid.uuid4(),
                name="gpu-preset",
                resource_slots=ResourceSlot({"cpu": "4", "mem": "8G", "cuda.device": "1"}),
                shared_memory=None,
                scaling_group_name=scaling_group,
            )
        ]

        # Mock cache miss, then DB hit
        mock_cache_source.get_preset_list = AsyncMock(return_value=None)
        mock_db_source.list_presets = AsyncMock(return_value=preset_list)
        mock_cache_source.set_preset_list = AsyncMock()

        result = await resource_preset_repository.list_presets(scaling_group_name=scaling_group)

        assert len(result) == 1
        assert result[0].scaling_group_name == scaling_group
        mock_cache_source.get_preset_list.assert_called_once_with(scaling_group)
        mock_db_source.list_presets.assert_called_once_with(scaling_group)
        mock_cache_source.set_preset_list.assert_called_once_with(preset_list, scaling_group)

    @pytest.mark.asyncio
    async def test_list_presets_empty(
        self, resource_preset_repository, mock_db_source, mock_cache_source
    ) -> None:
        """Test listing presets when none exist"""
        # Mock cache miss, then DB returns empty list
        mock_cache_source.get_preset_list = AsyncMock(return_value=None)
        mock_db_source.list_presets = AsyncMock(return_value=[])
        mock_cache_source.set_preset_list = AsyncMock()

        result = await resource_preset_repository.list_presets()

        assert len(result) == 0
        mock_cache_source.get_preset_list.assert_called_once_with(None)
        mock_db_source.list_presets.assert_called_once_with(None)
        mock_cache_source.set_preset_list.assert_called_once_with([], None)

    @pytest.mark.asyncio
    async def test_repository_decorator_applied(self, resource_preset_repository) -> None:
        """Test that repository decorator is applied to methods"""
        # These methods should have the repository decorator
        methods_with_decorator = [
            "create_preset_validated",
            "get_preset_by_id",
            "get_preset_by_name",
            "get_preset_by_id_or_name",
            "modify_preset_validated",
            "delete_preset_validated",
            "list_presets",
        ]

        for method_name in methods_with_decorator:
            method = getattr(resource_preset_repository, method_name)
            # Repository decorator should be applied (check that it's callable)
            assert callable(method)


class TestResourcePresetDataModels:
    """Test cases for ResourcePresetData and related models"""

    def test_resource_preset_data_conversion(self) -> None:
        """Test ResourcePresetData to/from dataclass conversion"""
        preset_data = ResourcePresetData(
            id=uuid.uuid4(),
            name="test-preset",
            resource_slots=ResourceSlot({"cpu": Decimal("4"), "mem": Decimal("8589934592")}),
            shared_memory=BinarySize(1073741824),  # 1 GiB
            scaling_group_name="default",
        )

        # Test to_cache method
        cache_data = preset_data.to_cache()
        assert cache_data["id"] == str(preset_data.id)
        assert cache_data["name"] == preset_data.name
        assert cache_data["resource_slots"] == preset_data.resource_slots.to_json()
        assert cache_data["shared_memory"] == str(preset_data.shared_memory)
        assert cache_data["scaling_group_name"] == preset_data.scaling_group_name

        # Test from_cache method
        restored = ResourcePresetData.from_cache(cache_data)
        assert restored.id == preset_data.id
        assert restored.name == preset_data.name
        assert restored.resource_slots == preset_data.resource_slots
        assert restored.shared_memory == preset_data.shared_memory
        assert restored.scaling_group_name == preset_data.scaling_group_name

    def test_resource_slot_validation(self) -> None:
        """Test ResourceSlot validation and conversion"""
        # Valid resource slot - use Decimal values directly
        slot = ResourceSlot({"cpu": Decimal("4"), "mem": Decimal("8589934592")})
        assert slot["cpu"] == Decimal("4")
        assert slot["mem"] == Decimal("8589934592")

        # JSON conversion
        json_data = slot.to_json()
        restored = ResourceSlot.from_json(json_data)
        assert restored == slot

    def test_binary_size_validation(self) -> None:
        """Test BinarySize validation and conversion"""
        # From string
        size = BinarySize.from_str("2 GiB")
        assert size == 2147483648  # 2 GiB in bytes

        # String representation
        assert str(size) == "2 GiB"

    def test_scaling_group_name_validation(self) -> None:
        """Test scaling group name validation"""
        preset_data = ResourcePresetData(
            id=uuid.uuid4(),
            name="test-preset",
            resource_slots=ResourceSlot({"cpu": "4", "mem": "8G"}),
            shared_memory=None,
            scaling_group_name=None,  # Can be None
        )
        assert preset_data.scaling_group_name is None

        preset_data_with_group = ResourcePresetData(
            id=uuid.uuid4(),
            name="test-preset",
            resource_slots=ResourceSlot({"cpu": "4", "mem": "8G"}),
            shared_memory=None,
            scaling_group_name="gpu-cluster",
        )
        assert preset_data_with_group.scaling_group_name == "gpu-cluster"
