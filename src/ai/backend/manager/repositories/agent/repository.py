import logging
from collections.abc import Sequence
from typing import Any, Mapping, cast

import sqlalchemy as sa
from sqlalchemy.orm import contains_eager

from ai.backend.common.clients.valkey_client.valkey_image.client import ValkeyImageClient
from ai.backend.common.clients.valkey_client.valkey_live.client import ValkeyLiveClient
from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.data.image.types import ScannedImage
from ai.backend.common.exception import BackendAIError
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.common.types import AgentId, ImageCanonical, ImageID
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.agent.types import (
    AgentData,
    AgentHeartbeatUpsert,
    UpsertResult,
)
from ai.backend.manager.data.image.types import ImageDataWithDetails, ImageIdentifier
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.agent.cache_source.cache_source import AgentCacheSource
from ai.backend.manager.repositories.agent.db_source.db_source import AgentDBSource
from ai.backend.manager.repositories.agent.stateful_source.stateful_source import (
    AgentStatefulSource,
)
from ai.backend.manager.repositories.agent.updaters import AgentStatusUpdaterSpec
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.resource_preset.utils import suppress_with_log

from .query import QueryCondition, QueryOrder

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


agent_repository_resilience = Resilience(
    policies=[
        MetricPolicy(MetricArgs(domain=DomainType.REPOSITORY, layer=LayerType.AGENT_REPOSITORY)),
        RetryPolicy(
            RetryArgs(
                max_retries=10,
                retry_delay=0.1,
                backoff_strategy=BackoffStrategy.FIXED,
                non_retryable_exceptions=(BackendAIError,),
            )
        ),
    ]
)


class AgentRepository:
    _db_source: AgentDBSource
    _cache_source: AgentCacheSource
    _stateful_source: AgentStatefulSource
    _config_provider: ManagerConfigProvider

    def __init__(
        self,
        db: ExtendedAsyncSAEngine,
        valkey_image: ValkeyImageClient,
        valkey_live: ValkeyLiveClient,
        valkey_stat: ValkeyStatClient,
        config_provider: ManagerConfigProvider,
    ) -> None:
        self._db_source = AgentDBSource(db)
        self._cache_source = AgentCacheSource(valkey_image, valkey_live, valkey_stat)
        self._stateful_source = AgentStatefulSource(valkey_image)
        self._config_provider = config_provider

    @agent_repository_resilience.apply()
    async def get_by_id(self, agent_id: AgentId) -> AgentData:
        return await self._db_source.get_by_id(agent_id)

    @agent_repository_resilience.apply()
    async def sync_installed_images(self, agent_id: AgentId) -> None:
        installed_image_info = await self._stateful_source.read_agent_installed_images(agent_id)
        image_identifiers = [
            ImageIdentifier(canonical=img.canonical, architecture=img.architecture)
            for img in installed_image_info
        ]
        images_data = await self._db_source.get_images_by_image_identifiers(image_identifiers)
        image_ids: list[ImageID] = list(images_data.keys())
        with suppress_with_log(
            [Exception], message=f"Failed to cache agent: {agent_id} to images: {image_ids}"
        ):
            await self._cache_source.set_agent_to_images(agent_id, image_ids)

    @agent_repository_resilience.apply()
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

    @agent_repository_resilience.apply()
    async def cleanup_agent_on_exit(self, agent_id: AgentId, spec: AgentStatusUpdaterSpec) -> None:
        with suppress_with_log(
            [Exception], message=f"Failed to remove last seen for agent: {agent_id}"
        ):
            await self._cache_source.remove_agent_last_seen(agent_id)

        updater = Updater[AgentRow](spec=spec, pk_value=agent_id)
        await self._db_source.update_agent_status_exit(updater)

        with suppress_with_log(
            [Exception], message=f"Failed to remove agent: {agent_id} from all images"
        ):
            await self._cache_source.remove_agent_from_all_images(agent_id)

    @agent_repository_resilience.apply()
    async def update_agent_status(self, agent_id: AgentId, spec: AgentStatusUpdaterSpec) -> None:
        updater = Updater[AgentRow](spec=spec, pk_value=agent_id)
        await self._db_source.update_agent_status(updater)

    # For compatibility with redis key made with image canonical strings
    # Use remove_agent_from_images instead of this if possible
    @agent_repository_resilience.apply()
    async def remove_agent_from_images_by_canonicals(
        self, agent_id: AgentId, image_canonicals: list[ImageCanonical]
    ) -> None:
        with suppress_with_log(
            [Exception],
            message=f"Failed to remove agent: {agent_id} from images: {image_canonicals}",
        ):
            await self._cache_source.remove_agent_from_images_by_canonicals(
                agent_id, image_canonicals
            )

    @agent_repository_resilience.apply()
    async def remove_agent_from_images(
        self, agent_id: AgentId, scanned_images: Mapping[ImageCanonical, ScannedImage]
    ) -> None:
        digest_list = [image.digest for image in scanned_images.values()]
        images: dict[ImageID, ImageDataWithDetails] = await self._db_source.get_images_by_digest(
            digest_list
        )
        with suppress_with_log(
            [Exception],
            message=f"Failed to remove agent: {agent_id} from images: {list(images.keys())}",
        ):
            await self._cache_source.remove_agent_from_images(agent_id, list(images.keys()))

    @agent_repository_resilience.apply()
    async def list_data(
        self,
        conditions: Sequence[QueryCondition],
        order_by: Sequence[QueryOrder] = tuple(),
    ) -> list[AgentData]:
        stmt: sa.sql.Select = (
            sa.select(AgentRow)
            .select_from(
                sa.join(
                    AgentRow,
                    KernelRow,
                    sa.and_(
                        AgentRow.id == KernelRow.agent,
                        KernelRow.status.in_(KernelStatus.resource_occupied_statuses()),
                    ),
                    isouter=True,
                )
            )
            .options(
                contains_eager(AgentRow.kernels),
            )
        )
        for cond in conditions:
            stmt = stmt.where(cond())

        if order_by:
            stmt = stmt.order_by(*order_by)

        async with self._db_source._db.begin_readonly_session() as db_session:
            result = await db_session.scalars(stmt)
            agent_rows = cast(list[AgentRow], result.unique().all())
            return [agent_row.to_data() for agent_row in agent_rows]

    @agent_repository_resilience.apply()
    async def update_gpu_alloc_map(self, agent_id: AgentId, alloc_map: Mapping[str, Any]) -> None:
        """Update GPU allocation map in cache."""
        with suppress_with_log(
            [Exception], message=f"Failed to update GPU alloc map for agent: {agent_id}"
        ):
            await self._cache_source.update_gpu_alloc_map(agent_id, alloc_map)
