"""
Tests for ResourcePresetRepository cache invalidation functionality.
Tests the repository layer with real database and Redis/Valkey operations.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.typed_validators import HostPortPair as HostPortPairModel
from ai.backend.common.types import AccessKey, BinarySize, ResourceSlot
from ai.backend.manager.data.resource_preset.types import ResourcePresetData
from ai.backend.manager.models.resource_preset import ResourcePresetRow
from ai.backend.manager.models.scaling_group import ScalingGroupOpts, ScalingGroupRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.repositories.resource_preset.creators import ResourcePresetCreatorSpec
from ai.backend.manager.repositories.resource_preset.repository import ResourcePresetRepository
from ai.backend.testutils.db import with_tables


class TestResourcePresetCacheInvalidation:
    """Test cases for ResourcePresetRepository cache invalidation with real DB and Redis"""

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        """Database connection with tables created. TRUNCATE CASCADE handles cleanup."""
        async with with_tables(
            database_connection,
            [ScalingGroupRow, ResourcePresetRow],
        ):
            yield database_connection

    @pytest.fixture
    async def test_scaling_group_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[str, None]:
        """Create test scaling group and return group name"""
        group_name = f"test-group-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as db_sess:
            scaling_group = ScalingGroupRow(
                name=group_name,
                description="Test scaling group for preset",
                is_active=True,
                driver="static",
                scheduler="fifo",
                scheduler_opts=ScalingGroupOpts(),
            )
            db_sess.add(scaling_group)
            await db_sess.flush()

        yield group_name

    @pytest.fixture
    async def sample_preset_creator(
        self,
        test_scaling_group_name: str,
    ) -> AsyncGenerator[Creator, None]:
        """Create sample resource preset creator for testing"""
        creator = Creator(
            spec=ResourcePresetCreatorSpec(
                name=f"test-preset-{uuid.uuid4().hex[:8]}",
                resource_slots=ResourceSlot({"cpu": "2", "mem": "4G"}),
                shared_memory="1 GiB",
                scaling_group_name=test_scaling_group_name,
            )
        )
        yield creator

    @pytest.fixture
    async def valkey_stat(
        self,
        redis_container: tuple[str, HostPortPairModel],
    ) -> AsyncGenerator[ValkeyStatClient, None]:
        """Create ValkeyStatClient instance with real Redis"""
        from ai.backend.common.types import ValkeyTarget

        redis_addr = redis_container[1]
        valkey_target = ValkeyTarget(
            addr=f"{redis_addr.host}:{redis_addr.port}",
            sentinel=None,
            service_name=None,
        )

        valkey_stat = await ValkeyStatClient.create(
            valkey_target=valkey_target,
            db_id=0,
            human_readable_name="test-valkey-stat",
        )
        yield valkey_stat

        # Cleanup Redis cache
        await valkey_stat.invalidate_all_resource_presets()
        await valkey_stat.close()

    @pytest.fixture
    async def resource_preset_repository(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        valkey_stat: ValkeyStatClient,
    ) -> AsyncGenerator[ResourcePresetRepository, None]:
        """Create ResourcePresetRepository instance with real database and Redis"""
        # Mock config provider
        mock_config_provider = MagicMock()
        mock_config_provider.legacy_etcd_config_loader.get_resource_slots = AsyncMock(
            return_value={"cpu", "mem", "cuda.device"}
        )

        repo = ResourcePresetRepository(
            db=db_with_cleanup,
            valkey_stat=valkey_stat,
            config_provider=mock_config_provider,
        )
        yield repo

    @pytest.mark.asyncio
    async def test_create_preset_invalidates_cache(
        self,
        resource_preset_repository: ResourcePresetRepository,
        sample_preset_creator: Creator,
    ) -> None:
        """Test that creating a preset invalidates all preset caches"""
        # Get reference to cache source and valkey stat
        cache_source = resource_preset_repository._cache_source
        # Create some cache entries before creating preset
        dummy_preset = ResourcePresetData(
            id=uuid.uuid4(),
            name="dummy-preset",
            resource_slots=ResourceSlot({"cpu": "1", "mem": "1G"}),
            shared_memory=int(BinarySize.from_str("512M")),
            scaling_group_name=None,
        )
        await cache_source.set_preset(dummy_preset)
        await cache_source.set_preset_list([dummy_preset], scaling_group=None)

        # Verify cache entries exist
        cached_preset = await cache_source.get_preset_by_id(dummy_preset.id)
        assert cached_preset is not None
        cached_list = await cache_source.get_preset_list(scaling_group=None)
        assert cached_list is not None

        # Create a new preset - this should invalidate all caches
        created_preset = await resource_preset_repository.create_preset_validated(
            sample_preset_creator
        )
        assert created_preset is not None

        # Verify all cache entries are invalidated (deleted)
        cached_preset_after = await cache_source.get_preset_by_id(dummy_preset.id)
        assert cached_preset_after is None

        cached_list_after = await cache_source.get_preset_list(scaling_group=None)
        assert cached_list_after is None

    @pytest.mark.asyncio
    async def test_invalidate_all_presets_deletes_all_keys(
        self,
        resource_preset_repository: ResourcePresetRepository,
    ) -> None:
        """Test that invalidate_all_presets deletes all preset-related cache keys"""
        cache_source = resource_preset_repository._cache_source
        # Create multiple cache entries of different types
        preset1 = ResourcePresetData(
            id=uuid.uuid4(),
            name="preset-1",
            resource_slots=ResourceSlot({"cpu": "2", "mem": "2G"}),
            shared_memory=int(BinarySize.from_str("1G")),
            scaling_group_name=None,
        )
        preset2 = ResourcePresetData(
            id=uuid.uuid4(),
            name="preset-2",
            resource_slots=ResourceSlot({"cpu": "4", "mem": "4G"}),
            shared_memory=int(BinarySize.from_str("2G")),
            scaling_group_name="test-group",
        )

        # Cache by ID and name
        await cache_source.set_preset(preset1)
        await cache_source.set_preset(preset2)

        # Cache lists
        await cache_source.set_preset_list([preset1], scaling_group=None)
        await cache_source.set_preset_list([preset2], scaling_group="test-group")

        # Cache check data (simulating check_presets cache)
        test_check_data = b'{"allowed": true}'
        test_access_key = AccessKey("test-access-key")
        await cache_source.set_check_presets_data(
            access_key=test_access_key,
            group="test-group",
            domain="test-domain",
            scaling_group=None,
            data=test_check_data,
        )

        # Verify caches exist
        assert await cache_source.get_preset_by_id(preset1.id) is not None
        assert await cache_source.get_preset_by_name(preset1.name) is not None
        assert await cache_source.get_preset_list(scaling_group=None) is not None
        assert (
            await cache_source.get_check_presets_data(
                access_key=test_access_key,
                group="test-group",
                domain="test-domain",
                scaling_group=None,
            )
            is not None
        )

        # Invalidate all presets
        await cache_source.invalidate_all_presets()

        # Verify all caches are deleted
        assert await cache_source.get_preset_by_id(preset1.id) is None
        assert await cache_source.get_preset_by_id(preset2.id) is None
        assert await cache_source.get_preset_by_name(preset1.name) is None
        assert await cache_source.get_preset_by_name(preset2.name) is None
        assert await cache_source.get_preset_list(scaling_group=None) is None
        assert await cache_source.get_preset_list(scaling_group="test-group") is None
        assert (
            await cache_source.get_check_presets_data(
                access_key=test_access_key,
                group="test-group",
                domain="test-domain",
                scaling_group=None,
            )
            is None
        )

    @pytest.mark.asyncio
    async def test_invalidate_all_presets_handles_no_keys(
        self,
        resource_preset_repository: ResourcePresetRepository,
    ) -> None:
        """Test that invalidate_all_presets handles the case when no cache keys exist"""
        cache_source = resource_preset_repository._cache_source

        # Ensure cache is empty by invalidating first
        await cache_source.invalidate_all_presets()

        # Should not raise any errors when no keys exist
        await cache_source.invalidate_all_presets()

    @pytest.mark.asyncio
    async def test_valkey_stat_invalidate_all_resource_presets(
        self,
        resource_preset_repository: ResourcePresetRepository,
    ) -> None:
        """Test ValkeyStatClient.invalidate_all_resource_presets method directly"""
        valkey_stat = resource_preset_repository._cache_source._valkey_stat

        # Create cache entries using raw valkey_stat methods
        test_data = b'{"test": "data"}'
        await valkey_stat.set_resource_preset_by_id_and_name(
            "test-id-1", "test-name-1", test_data, expire_sec=60
        )
        await valkey_stat.set_resource_preset_by_id_and_name(
            "test-id-2", "test-name-2", test_data, expire_sec=60
        )
        await valkey_stat.set_resource_preset_list(None, test_data, expire_sec=60)
        await valkey_stat.set_resource_preset_list("test-group", test_data, expire_sec=60)
        await valkey_stat.set_resource_preset_check_data(
            "test-key", "test-group", "test-domain", None, test_data, expire_sec=60
        )

        # Verify entries exist
        assert await valkey_stat.get_resource_preset_by_id("test-id-1") is not None
        assert await valkey_stat.get_resource_preset_by_name("test-name-1") is not None
        assert await valkey_stat.get_resource_preset_list(None) is not None
        assert (
            await valkey_stat.get_resource_preset_check_data(
                "test-key", "test-group", "test-domain", None
            )
            is not None
        )

        # Invalidate all
        await valkey_stat.invalidate_all_resource_presets()

        # Verify all entries are deleted
        assert await valkey_stat.get_resource_preset_by_id("test-id-1") is None
        assert await valkey_stat.get_resource_preset_by_id("test-id-2") is None
        assert await valkey_stat.get_resource_preset_by_name("test-name-1") is None
        assert await valkey_stat.get_resource_preset_by_name("test-name-2") is None
        assert await valkey_stat.get_resource_preset_list(None) is None
        assert await valkey_stat.get_resource_preset_list("test-group") is None
        assert (
            await valkey_stat.get_resource_preset_check_data(
                "test-key", "test-group", "test-domain", None
            )
            is None
        )
