from collections.abc import Collection, Sequence
from typing import Optional, cast

import sqlalchemy as sa
from sqlalchemy.orm import contains_eager

from ai.backend.common.metrics.metric import LayerType
from ai.backend.common.types import AgentId
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.agent.types import AgentData, AgentDataExtended
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.decorators.repository_decorator import (
    create_layer_aware_repository_decorator,
)
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

from .query import QueryCondition, QueryOrder

# Layer-specific decorator for agent repository
repository_decorator = create_layer_aware_repository_decorator(LayerType.AGENT)


class AgentRepository:
    _db: ExtendedAsyncSAEngine
    _config_provider: ManagerConfigProvider

    def __init__(self, db: ExtendedAsyncSAEngine, config_provider: ManagerConfigProvider) -> None:
        self._db = db
        self._config_provider = config_provider

    @repository_decorator()
    async def get_by_id(self, agent_id: AgentId) -> Optional[AgentData]:
        async with self._db.begin_readonly_session() as db_session:
            agent_row = await db_session.scalar(sa.select(AgentRow).where(AgentRow.id == agent_id))
            agent_row = cast(Optional[AgentRow], agent_row)
            if agent_row is None:
                return None
            return agent_row.to_data()

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

        async with self._db.begin_readonly_session() as db_session:
            result = await db_session.scalars(stmt)
            agent_rows = cast(list[AgentRow], result.all())
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
        async with self._db.begin_readonly_session() as db_session:
            result = await db_session.scalars(stmt)
            agent_rows = cast(list[AgentRow], result.unique().all())
            return [agent_row.to_extended_data(known_slot_types) for agent_row in agent_rows]
