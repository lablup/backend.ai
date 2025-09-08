import logging
from decimal import Decimal
from typing import Mapping, Optional
from uuid import UUID

import trafaret as t

from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.metrics.metric import LayerType
from ai.backend.common.types import AccessKey, ResourceSlot
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.resource_preset.types import ResourcePresetData
from ai.backend.manager.decorators.repository_decorator import (
    create_layer_aware_repository_decorator,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.services.resource_preset.types import (
    ResourcePresetCreator,
    ResourcePresetModifier,
)

from .cache_source.cache_source import ResourcePresetCacheSource
from .db_source.db_source import ResourcePresetDBSource
from .types import CheckPresetsResult
from .utils import suppress_with_log

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

# Layer-specific decorator for resource_preset repository
repository_decorator = create_layer_aware_repository_decorator(LayerType.RESOURCE_PRESET)


class ResourcePresetRepository:
    """Repository that orchestrates between DB and cache sources for resource preset operations."""

    _db_source: ResourcePresetDBSource
    _cache_source: ResourcePresetCacheSource
    _config_provider: ManagerConfigProvider

    def __init__(
        self,
        db: ExtendedAsyncSAEngine,
        valkey_stat: ValkeyStatClient,
        config_provider: ManagerConfigProvider,
    ) -> None:
        self._db_source = ResourcePresetDBSource(db)
        self._cache_source = ResourcePresetCacheSource(valkey_stat)
        self._config_provider = config_provider

    @repository_decorator()
    async def create_preset_validated(self, creator: ResourcePresetCreator) -> ResourcePresetData:
        """
        Creates a new resource preset.
        Raises ResourcePresetConflict if a preset with the same name and scaling group already exists.
        """
        preset = await self._db_source.create_preset(creator)
        with suppress_with_log(
            [Exception], message="Failed to invalidate cache after preset creation"
        ):
            await self._cache_source.invalidate_all_presets()
        return preset

    @repository_decorator()
    async def get_preset_by_id(self, preset_id: UUID) -> ResourcePresetData:
        """
        Gets a resource preset by ID.
        Raises ResourcePresetNotFound if the preset doesn't exist.
        """
        # Try cache first
        with suppress_with_log([Exception], message=f"Failed to get preset {preset_id} from cache"):
            preset = await self._cache_source.get_preset_by_id(preset_id)
            if preset:
                return preset

        # Fallback to DB
        preset = await self._db_source.get_preset_by_id(preset_id)
        with suppress_with_log([Exception], message=f"Failed to cache preset {preset_id}"):
            await self._cache_source.set_preset(preset)
        return preset

    @repository_decorator()
    async def get_preset_by_name(self, name: str) -> ResourcePresetData:
        """
        Gets a resource preset by name.
        Raises ResourcePresetNotFound if the preset doesn't exist.
        """
        # Try cache first
        with suppress_with_log([Exception], message=f"Failed to get preset '{name}' from cache"):
            preset = await self._cache_source.get_preset_by_name(name)
            if preset:
                return preset

        # Fallback to DB
        preset = await self._db_source.get_preset_by_name(name)
        with suppress_with_log([Exception], message=f"Failed to cache preset '{name}'"):
            await self._cache_source.set_preset(preset)
        return preset

    @repository_decorator()
    async def get_preset_by_id_or_name(
        self, preset_id: Optional[UUID], name: Optional[str]
    ) -> ResourcePresetData:
        """
        Gets a resource preset by ID or name.
        ID takes precedence if both are provided.
        Raises ResourcePresetNotFound if the preset doesn't exist.
        """
        return await self._db_source.get_preset_by_id_or_name(preset_id, name)

    @repository_decorator()
    async def modify_preset_validated(
        self, preset_id: Optional[UUID], name: Optional[str], modifier: ResourcePresetModifier
    ) -> ResourcePresetData:
        """
        Modifies an existing resource preset.
        Raises ResourcePresetNotFound if the preset doesn't exist.
        """
        preset = await self._db_source.modify_preset(preset_id, name, modifier)
        with suppress_with_log(
            [Exception], message="Failed to invalidate cache after preset modification"
        ):
            await self._cache_source.invalidate_preset(preset_id, name)
        return preset

    @repository_decorator()
    async def delete_preset_validated(
        self, preset_id: Optional[UUID], name: Optional[str]
    ) -> ResourcePresetData:
        """
        Deletes a resource preset.
        Returns the deleted preset data.
        Raises ObjectNotFound if the preset doesn't exist.
        """
        preset = await self._db_source.delete_preset(preset_id, name)
        with suppress_with_log(
            [Exception], message="Failed to invalidate cache after preset deletion"
        ):
            await self._cache_source.invalidate_preset(preset_id, name)
        return preset

    @repository_decorator()
    async def list_presets(
        self, scaling_group_name: Optional[str] = None
    ) -> list[ResourcePresetData]:
        """
        Lists all resource presets.
        If scaling_group_name is provided, returns presets for that scaling group and global presets.
        """
        # Try cache first
        with suppress_with_log([Exception], message="Failed to get preset list from cache"):
            presets = await self._cache_source.get_preset_list(scaling_group_name)
            if presets is not None:
                return presets

        # Fallback to DB
        await self._config_provider.legacy_etcd_config_loader.get_resource_slots()
        presets = await self._db_source.list_presets(scaling_group_name)

        # Cache the result
        with suppress_with_log([Exception], message="Failed to cache preset list"):
            await self._cache_source.set_preset_list(presets, scaling_group_name)

        return presets

    @repository_decorator()
    async def check_presets(
        self,
        access_key: AccessKey,
        user_id: UUID,
        group_name: str,
        domain_name: str,
        resource_policy: Mapping[str, str],
        scaling_group: Optional[str] = None,
    ) -> CheckPresetsResult:
        """
        Check resource presets availability and resource limits.
        """
        # Get configuration values
        known_slot_types = (
            await self._config_provider.legacy_etcd_config_loader.get_resource_slots()
        )
        # Try to get from cache first
        with suppress_with_log([Exception], message="Failed to get check presets data from cache"):
            cached_data = await self._cache_source.get_check_presets_data(
                access_key, group_name, domain_name, scaling_group
            )
            if cached_data:
                log.info(
                    "Cache hit for check_presets: {}, {}, {}", access_key, group_name, domain_name
                )
                return CheckPresetsResult.from_cache(cached_data)
        log.info(
            "Cache miss for check_presets, fetching from DB, {}, {}, {}",
            access_key,
            group_name,
            domain_name,
        )

        group_resource_visibility = await self._config_provider.legacy_etcd_config_loader.get_raw(
            "config/api/resources/group_resource_visibility"
        )
        group_resource_visibility = t.ToBool().check(group_resource_visibility)

        # Get all data from DB source
        db_data = await self._db_source.check_presets_data(
            access_key,
            user_id,
            group_name,
            domain_name,
            resource_policy,
            known_slot_types,
            scaling_group,
        )

        # Process the data and build response

        # Apply group resource visibility settings
        if not group_resource_visibility:
            nan_slots = ResourceSlot({k: Decimal("NaN") for k in db_data.known_slot_types.keys()})
            group_limits = nan_slots
            group_occupied = nan_slots
            group_remaining = nan_slots
        else:
            group_limits = db_data.keypair_data.group_limits
            group_occupied = db_data.keypair_data.group_occupied
            group_remaining = db_data.keypair_data.group_remaining

        result = CheckPresetsResult(
            presets=db_data.presets,
            keypair_limits=db_data.keypair_data.limits,
            keypair_using=db_data.keypair_data.occupied,
            keypair_remaining=db_data.keypair_data.remaining,
            group_limits=group_limits,
            group_using=group_occupied,
            group_remaining=group_remaining,
            scaling_group_remaining=db_data.keypair_data.scaling_group_remaining,
            scaling_groups=db_data.per_sgroup_data,
        )

        # Cache the result
        with suppress_with_log([Exception], message="Failed to cache check presets data"):
            cache_data = result.to_cache()
            await self._cache_source.set_check_presets_data(
                access_key,
                group_name,
                domain_name,
                scaling_group,
                cache_data,
            )

        return result
