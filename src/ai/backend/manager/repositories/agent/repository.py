import asyncio
import logging
import zlib
from collections.abc import Mapping
from typing import Any, Optional

from ai.backend.common import msgpack
from ai.backend.common.clients.valkey_client.valkey_image.client import ValkeyImageClient
from ai.backend.common.clients.valkey_client.valkey_live.client import ValkeyLiveClient
from ai.backend.common.metrics.metric import LayerType
from ai.backend.common.types import AgentId
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.agent_cache import AgentRPCCache
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.agent.types import (
    AgentHeartbeatUpsert,
    AgentStateSyncData,
    UpsertResult,
)
from ai.backend.manager.decorators.repository_decorator import (
    create_layer_aware_repository_decorator,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.agent.cache_source.cache_source import AgentCacheSource
from ai.backend.manager.repositories.agent.db_source.db_source import AgentDBSource
from ai.backend.manager.services.agent.types import AgentData

# Layer-specific decorator for agent repository
repository_decorator = create_layer_aware_repository_decorator(LayerType.AGENT)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class AgentRepository:
    _db_source: AgentDBSource
    _cache_source: AgentCacheSource
    _config_provider: ManagerConfigProvider
    _heartbeat_lock: asyncio.Lock

    def __init__(
        self,
        db: ExtendedAsyncSAEngine,
        valkey_image: ValkeyImageClient,
        valkey_live: ValkeyLiveClient,
        config_provider: ManagerConfigProvider,
        agent_cache: AgentRPCCache,
    ) -> None:
        self._db_source = AgentDBSource(db)
        self._cache_source = AgentCacheSource(valkey_image, valkey_live)
        self._config_provider = config_provider
        self._heartbeat_lock = asyncio.Lock()
        self._agent_cache = agent_cache

    @repository_decorator()
    async def get_by_id(self, agent_id: AgentId) -> Optional[AgentData]:
        return await self._db_source.get_by_id(agent_id)

    @repository_decorator()
    async def add_agent_to_images(self, agent_id: AgentId, images) -> None:
        images = msgpack.unpackb(zlib.decompress(images))
        image_canonicals = set(img_info[0] for img_info in images)
        await self._cache_source.set_agent_to_images(agent_id, list(image_canonicals))

    @repository_decorator()
    async def sync_agent_heartbeat(
        self, agent_id: AgentId, agent_info: Mapping[Any, Any], state_sync_data: AgentStateSyncData
    ) -> UpsertResult:
        await self._cache_source.update_agent_last_seen(agent_id, state_sync_data.now)

        upsert_data = AgentHeartbeatUpsert.from_agent_info(
            agent_id=agent_id,
            agent_info=agent_info,
            heartbeat_received=state_sync_data.now,
        )

        upsert_result = await self._db_source.upsert_agent_with_state(upsert_data)
        if upsert_result.need_agent_cache_update:
            self._agent_cache.update(
                agent_id, state_sync_data.current_addr, state_sync_data.public_key
            )
        if upsert_result.need_resource_slot_update:
            await self._config_provider.legacy_etcd_config_loader.update_resource_slots(
                state_sync_data.slot_key_and_units
            )

        return upsert_result
