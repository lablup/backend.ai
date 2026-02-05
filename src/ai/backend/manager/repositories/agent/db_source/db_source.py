import logging
from collections.abc import Sequence
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import selectinload, with_loader_criteria

from ai.backend.common.exception import AgentNotFound
from ai.backend.common.resource.types import AgentResourceData
from ai.backend.common.types import AgentId, ImageID, ResourceSlot
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.data.agent.types import (
    AgentData,
    AgentDetailData,
    AgentHeartbeatUpsert,
    AgentListResult,
    AgentStatus,
    UpsertResult,
)
from ai.backend.manager.data.image.types import ImageDataWithDetails, ImageIdentifier
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.errors.resource import ScalingGroupNotFound
from ai.backend.manager.models.agent import ADMIN_PERMISSIONS as ADMIN_AGENT_PERMISSIONS
from ai.backend.manager.models.agent import AgentRow, agents
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.scaling_group import ScalingGroupRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.agent.updaters import AgentStatusUpdaterSpec
from ai.backend.manager.repositories.base.querier import BatchQuerier, execute_batch_querier
from ai.backend.manager.repositories.base.updater import Updater, execute_updater

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class AgentDBSource:
    """Database source for agent-related operations."""

    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    async def get_images_by_image_identifiers(
        self, image_identifiers: list[ImageIdentifier]
    ) -> dict[ImageID, ImageDataWithDetails]:
        async with self._db.begin_readonly_session() as db_session:
            identifier_tuples = [
                (identifier.canonical, identifier.architecture) for identifier in image_identifiers
            ]

            query = (
                sa.select(ImageRow)
                .where(sa.tuple_(ImageRow.name, ImageRow.architecture).in_(identifier_tuples))
                .options(selectinload(ImageRow.aliases))
            )
            image_rows = list((await db_session.scalars(query)).all())
            images_data: dict[ImageID, ImageDataWithDetails] = {}
            for image_row in image_rows:
                images_data[ImageID(image_row.id)] = image_row.to_detailed_dataclass()
            return images_data

    async def get_images_by_digest(self, digests: list[str]) -> dict[ImageID, ImageDataWithDetails]:
        async with self._db.begin_readonly_session() as db_session:
            query = (
                sa.select(ImageRow)
                .where(ImageRow.config_digest.in_(digests))
                .options(selectinload(ImageRow.aliases))
            )
            results = list((await db_session.scalars(query)).all())
            images_data: dict[ImageID, ImageDataWithDetails] = {}
            for image_row in results:
                images_data[ImageID(image_row.id)] = image_row.to_detailed_dataclass()
            return images_data

    async def get_by_id(self, agent_id: AgentId) -> AgentData:
        async with self._db.begin_readonly_session() as db_session:
            agent_row: AgentRow | None = await db_session.scalar(
                sa.select(AgentRow)
                .where(AgentRow.id == agent_id)
                .options(selectinload(AgentRow.kernels))
            )
            if agent_row is None:
                log.error("Agent with id {} not found", agent_id)
                raise AgentNotFound(f"Agent with id {agent_id} not found")
            return agent_row.to_data()

    async def _check_scaling_group_exists(
        self, session: "AsyncSession", scaling_group_name: str
    ) -> None:
        scaling_group_row = await session.scalar(
            sa.select(ScalingGroupRow).where(ScalingGroupRow.name == scaling_group_name)
        )
        if not scaling_group_row:
            log.error("Scaling group named [{}] does not exist.", scaling_group_name)
            raise ScalingGroupNotFound(scaling_group_name)

    async def upsert_agent_with_state(self, upsert_data: AgentHeartbeatUpsert) -> UpsertResult:
        async with self._db.begin_session() as session:
            await self._check_scaling_group_exists(session, upsert_data.metadata.scaling_group)

            query = (
                sa.select(AgentRow).where(AgentRow.id == upsert_data.metadata.id).with_for_update()
            )
            row: AgentRow | None = await session.scalar(query)
            agent_data = row.to_heartbeat_update_data() if row is not None else None
            upsert_result = UpsertResult.from_state_comparison(agent_data, upsert_data)

            stmt = pg_insert(agents).values(upsert_data.insert_fields)
            final_query = stmt.on_conflict_do_update(
                index_elements=["id"], set_=upsert_data.update_fields
            )

            await session.execute(final_query)

            return upsert_result

    async def update_agent_status_exit(self, updater: Updater[AgentRow]) -> None:
        async with self._db.begin_session() as session:
            fetch_query = (
                sa.select(AgentRow.status)
                .select_from(AgentRow)
                .where(AgentRow.id == updater.pk_value)
                .with_for_update()
            )
            prev_status = await session.scalar(fetch_query)
            if prev_status in (None, AgentStatus.LOST, AgentStatus.TERMINATED):
                return

            spec = updater.spec
            if isinstance(spec, AgentStatusUpdaterSpec):
                if spec.status == AgentStatus.LOST:
                    log.warning("agent {0} heartbeat timeout detected.", updater.pk_value)
                elif spec.status == AgentStatus.TERMINATED:
                    log.info("agent {0} has terminated.", updater.pk_value)

            await execute_updater(session, updater)

    async def update_agent_status(self, updater: Updater[AgentRow]) -> None:
        async with self._db.begin_session() as session:
            await execute_updater(session, updater)

    async def get_agent_resource_slots(
        self,
        agent_ids: Sequence[AgentId],
    ) -> dict[AgentId, AgentResourceData]:
        """Calculates resource usage data for the specified agents.

        Args:
            agent_ids: List of agent IDs to calculate resources for.
        Returns:
            A mapping from agent ID to AgentResourceData.
        """
        async with self._db.begin_readonly_session() as db_sess:
            query = (
                sa.select(AgentRow)
                .where(AgentRow.id.in_(agent_ids))
                .options(
                    selectinload(AgentRow.kernels),
                    with_loader_criteria(
                        KernelRow,
                        KernelRow.status.in_(KernelStatus.resource_occupied_statuses()),
                    ),
                )
            )
            result: dict[AgentId, AgentResourceData] = {}
            agent_rows: list[AgentRow] = list((await db_sess.scalars(query)).all())
            for agent_row in agent_rows:
                agent_id = AgentId(agent_row.id)
                capacity_slots = agent_row.available_slots or ResourceSlot()
                used_slots = agent_row.actual_occupied_slots()
                free_slots = capacity_slots - used_slots
                result[agent_id] = AgentResourceData(
                    used_slots=used_slots,
                    free_slots=free_slots,
                    capacity_slots=capacity_slots,
                )

            return result

    async def search_agents(
        self,
        querier: BatchQuerier,
    ) -> AgentListResult:
        """Searches agents with total count."""

        async with self._db.begin_readonly_session() as db_sess:
            query = sa.select(AgentRow).options(
                selectinload(AgentRow.kernels),
                with_loader_criteria(
                    KernelRow,
                    KernelRow.status.in_(KernelStatus.resource_occupied_statuses()),
                ),
            )

            result = await execute_batch_querier(
                db_sess,
                query,
                querier,
            )
            agent_rows: list[AgentRow] = [row.AgentRow for row in result.rows]
            items = [agent_row.to_data() for agent_row in agent_rows]
            admin_permissions = list(ADMIN_AGENT_PERMISSIONS)
            agents_with_permissions = [
                AgentDetailData(agent=agent_data, permissions=admin_permissions)
                for agent_data in items
            ]

            return AgentListResult(
                items=agents_with_permissions,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )
