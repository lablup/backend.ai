from typing import cast

import sqlalchemy as sa

from ai.backend.common.types import RedisConnectionInfo
from ai.backend.manager.config import SharedConfig
from ai.backend.manager.models.resource_preset import ResourcePresetRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.registry import AgentRegistry
from ai.backend.manager.services.resource.actions.list_presets import (
    ListResourcePresetsAction,
    ListResourcePresetsResult,
)


class ResourceService:
    _db: ExtendedAsyncSAEngine
    _shared_config: SharedConfig
    _agent_registry: AgentRegistry
    _redis_stat: RedisConnectionInfo

    # TODO: 인자들 한 타입으로 묶을 것.
    def __init__(
        self,
        db: ExtendedAsyncSAEngine,
        agent_registry: AgentRegistry,
        redis_stat: RedisConnectionInfo,
        shared_config: SharedConfig,
    ) -> None:
        self._db = db
        self._agent_registry = agent_registry
        self._redis_stat = redis_stat
        self._shared_config = shared_config

    async def list_presets(self, action: ListResourcePresetsAction) -> ListResourcePresetsResult:
        # TODO: Remove this?
        await self._shared_config.get_resource_slots()

        async with self._db.begin_readonly_session() as db_session:
            query = sa.select(ResourcePresetRow)
            query_condition = ResourcePresetRow.scaling_group_name.is_(sa.null())
            scaling_group_name = action.scaling_group
            if scaling_group_name is not None:
                query_condition = sa.or_(
                    query_condition, ResourcePresetRow.scaling_group_name == scaling_group_name
                )
            query = query.where(query_condition)
            presets = []
            async for row in await db_session.stream_scalars(query):
                row = cast(ResourcePresetRow, row)
                preset_slots = row.resource_slots.normalize_slots(ignore_unknown=True)
                presets.append({
                    "id": str(row.id),
                    "name": row.name,
                    "shared_memory": str(row.shared_memory) if row.shared_memory else None,
                    "resource_slots": preset_slots.to_json(),
                })

            return ListResourcePresetsResult(presets=presets)
