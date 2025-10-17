import logging
import zlib
from collections.abc import Collection, Sequence
from typing import cast

import sqlalchemy as sa
from sqlalchemy.orm import contains_eager

from ai.backend.common import msgpack
from ai.backend.common.clients.valkey_client.valkey_image.client import ValkeyImageClient
from ai.backend.common.clients.valkey_client.valkey_live.client import ValkeyLiveClient
from ai.backend.common.metrics.metric import LayerType
from ai.backend.common.types import AgentId
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.agent.modifier import AgentStatusModifier
from ai.backend.manager.data.agent.types import (
    AgentData,
    AgentDataExtended,
    AgentHeartbeatUpsert,
    UpsertResult,
)
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.decorators.repository_decorator import (
    create_layer_aware_repository_decorator,
)
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.agent.cache_source.cache_source import AgentCacheSource
from ai.backend.manager.repositories.agent.db_source.db_source import AgentDBSource
from ai.backend.manager.repositories.resource_preset.utils import suppress_with_log

from .query import QueryCondition, QueryOrder

# Layer-specific decorator for agent repository
repository_decorator = create_layer_aware_repository_decorator(LayerType.AGENT)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class AgentRepository:
    _db_source: AgentDBSource
    _cache_source: AgentCacheSource
    _config_provider: ManagerConfigProvider

    def __init__(
        self,
        db: ExtendedAsyncSAEngine,
        valkey_image: ValkeyImageClient,
        valkey_live: ValkeyLiveClient,
        config_provider: ManagerConfigProvider,
    ) -> None:
        self._db_source = AgentDBSource(db)
        self._cache_source = AgentCacheSource(valkey_image, valkey_live)
        self._config_provider = config_provider

    @repository_decorator()
    async def get_by_id(self, agent_id: AgentId) -> AgentData:
        return await self._db_source.get_by_id(agent_id)

    @repository_decorator()
    async def add_agent_to_images(self, agent_id: AgentId, images) -> None:
        images = msgpack.unpackb(zlib.decompress(images))
        image_canonicals = set(img_info[0] for img_info in images)
        with suppress_with_log(
            [Exception], message=f"Failed to cache agent: {agent_id} to images: {image_canonicals}"
        ):
            await self._cache_source.set_agent_to_images(agent_id, list(image_canonicals))

    @repository_decorator()
    async def sync_agent_heartbeat(
        self,
        agent_id: AgentId,
        upsert_data: AgentHeartbeatUpsert,
    ) -> UpsertResult:
        with suppress_with_log(
            [Exception], message=f"Failed to update last seen for agent: {agent_id}"
        ):
            await self._cache_source.update_agent_last_seen(
                agent_id, upsert_data.heartbeat_received
            )

        upsert_result = await self._db_source.upsert_agent_with_state(upsert_data)
        if upsert_result.need_resource_slot_update:
            await self._config_provider.legacy_etcd_config_loader.update_resource_slots(
                upsert_data.resource_info.slot_key_and_units
            )

        return upsert_result

    @repository_decorator()
    async def cleanup_agent_on_exit(self, agent_id: AgentId, modifier: AgentStatusModifier) -> None:
        with suppress_with_log(
            [Exception], message=f"Failed to remove last seen for agent: {agent_id}"
        ):
            await self._cache_source.remove_agent_last_seen(agent_id)

        await self._db_source.update_agent_status_exit(agent_id, modifier)

        with suppress_with_log(
            [Exception], message=f"Failed to remove agent: {agent_id} from all images"
        ):
            await self._cache_source.remove_agent_from_all_images(agent_id)

    @repository_decorator()
    async def update_agent_status(self, agent_id: AgentId, modifier: AgentStatusModifier) -> None:
        await self._db_source.update_agent_status(agent_id, modifier)

    @repository_decorator()
    async def remove_agent_from_images(
        self, agent_id: AgentId, image_canonicals: list[str]
    ) -> None:
        with suppress_with_log(
            [Exception],
            message=f"Failed to remove agent: {agent_id} from images: {image_canonicals}",
        ):
            await self._cache_source.remove_agent_from_images(agent_id, image_canonicals)

    @repository_decorator()
    async def list_data(
        self,
        conditions: Sequence[QueryCondition],
        order_by: Sequence[QueryOrder] = tuple(),
    ) -> list[AgentData]:
        stmt: sa.sql.Select = sa.select(AgentRow)
        for cond in conditions:
            stmt = cond(stmt)

        if order_by:
            stmt = stmt.order_by(*order_by)

        async with self._db_source._db.begin_readonly_session() as db_session:
            result = await db_session.scalars(stmt)
            agent_rows = cast(list[AgentRow], result.unique().all())
            return [agent_row.to_data() for agent_row in agent_rows]

    @repository_decorator()
    async def list_extended_data(
        self,
        conditions: Sequence[QueryCondition],
        order_by: Sequence[QueryOrder] = tuple(),
        *,
        kernel_statuses: Collection[KernelStatus] = (KernelStatus.RUNNING,),
    ) -> list[AgentDataExtended]:
        stmt: sa.sql.Select = (
            sa.select(AgentRow)
            .select_from(
                sa.join(
                    AgentRow,
                    KernelRow,
                    sa.and_(AgentRow.id == KernelRow.agent, KernelRow.status.in_(kernel_statuses)),
                    isouter=True,
                )
            )
            .options(
                contains_eager(AgentRow.kernels),
            )
        )
        for cond in conditions:
            stmt = cond(stmt)

        if order_by:
            stmt = stmt.order_by(*order_by)

        known_slot_types = (
            await self._config_provider.legacy_etcd_config_loader.get_resource_slots()
        )
        async with self._db_source._db.begin_readonly_session() as db_session:
            result = await db_session.scalars(stmt)
            agent_rows = cast(list[AgentRow], result.unique().all())
            return [agent_row.to_extended_data(known_slot_types) for agent_row in agent_rows]
