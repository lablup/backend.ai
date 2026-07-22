from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import selectinload

from ai.backend.common.exception import AgentNotFound
from ai.backend.common.identifier.resource_group import ResourceGroupID
from ai.backend.common.types import AgentId, ImageID
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
from ai.backend.manager.data.kernel.types import KernelInfo, KernelStatus
from ai.backend.manager.errors.agent import AgentHasConflictingSessions
from ai.backend.manager.errors.resource import UnresolvableResourceGroup
from ai.backend.manager.models.agent import ADMIN_PERMISSIONS as ADMIN_AGENT_PERMISSIONS
from ai.backend.manager.models.agent import AgentRow, agents
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.resource_slot import AgentResourceRow
from ai.backend.manager.models.scaling_group import ScalingGroupRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.agent.updaters import AgentStatusUpdaterSpec
from ai.backend.manager.repositories.base import BulkUpserter, execute_bulk_upserter
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
        async with self._db.begin_readonly_session_read_committed() as db_session:
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
        async with self._db.begin_readonly_session_read_committed() as db_session:
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
        async with self._db.begin_readonly_session_read_committed() as db_session:
            agent_row: AgentRow | None = await db_session.scalar(
                sa.select(AgentRow)
                .where(AgentRow.id == agent_id)
                .options(
                    selectinload(AgentRow.agent_resource_rows).joinedload(
                        AgentResourceRow.slot_type_row
                    )
                )
            )
            if agent_row is None:
                log.error("Agent with id {} not found", agent_id)
                raise AgentNotFound(f"Agent with id {agent_id} not found")
            return agent_row.to_data()

    async def upsert_agent_with_state(self, upsert_data: AgentHeartbeatUpsert) -> UpsertResult:
        async with self._db.begin_session_read_committed() as session:
            query = (
                sa.select(AgentRow).where(AgentRow.id == upsert_data.metadata.id).with_for_update()
            )
            row: AgentRow | None = await session.scalar(query)
            agent_data = row.to_heartbeat_update_data() if row is not None else None
            upsert_result = UpsertResult.from_state_comparison(agent_data, upsert_data)

            if row is None:
                await self._insert_new_agent(session, upsert_data)
            else:
                await session.execute(
                    sa.update(agents)
                    .where(agents.c.id == upsert_data.metadata.id)
                    .values(upsert_data.update_fields)
                )

            return upsert_result

    async def _insert_new_agent(
        self, session: AsyncSession, upsert_data: AgentHeartbeatUpsert
    ) -> None:
        resource_group_name = upsert_data.metadata.scaling_group
        group_filter: sa.ColumnElement[bool]
        group_order: sa.ColumnElement[Any]
        if resource_group_name is not None:
            group_filter = sa.or_(
                ScalingGroupRow.name == resource_group_name,
                ScalingGroupRow.is_default,
            )
            group_order = sa.case((ScalingGroupRow.name == resource_group_name, 0), else_=1)
        else:
            group_filter = ScalingGroupRow.is_default.is_(True)
            group_order = sa.asc(ScalingGroupRow.name)
        group_select = (
            sa.select(
                *[
                    sa.literal(value, type_=agents.c[key].type).label(key)
                    for key, value in upsert_data.insert_fields.items()
                ],
                ScalingGroupRow.name.label("scaling_group"),
                ScalingGroupRow.id.label("resource_group_id"),
            )
            .select_from(ScalingGroupRow)
            .where(group_filter)
            .order_by(group_order)
            .limit(1)
        )
        stmt = (
            pg_insert(agents)
            .from_select(
                [*upsert_data.insert_fields.keys(), "scaling_group", "resource_group_id"],
                group_select,
            )
            # Guard a rare race where a concurrent registration inserted first
            .on_conflict_do_update(
                index_elements=["id"],
                set_={**upsert_data.update_fields},
            )
            .returning(agents.c.id)
        )
        affected = (await session.execute(stmt)).scalar_one_or_none()
        if affected is None:
            if resource_group_name is not None:
                raise UnresolvableResourceGroup(
                    f"Scaling group '{resource_group_name}' not found "
                    "and no default scaling group is set."
                )
            raise UnresolvableResourceGroup(
                "No initial resource group name is configured and no default scaling group is set."
            )

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

    async def update_resource_group(
        self,
        agent_id: AgentId,
        resource_group_id: ResourceGroupID,
        *,
        force: bool,
    ) -> list[KernelInfo]:
        """
        Change the agent's resource group, gating on the kernels running on it.

        Finds the active kernels on the agent. If any exist and ``force`` is not
        set, raises without changing anything. Otherwise updates the agent's group
        (name + id columns) and returns those kernels so the caller can transition
        their sessions. The check and the update run in one transaction.
        """
        active_statuses = (
            KernelStatus.resource_occupied_statuses() | KernelStatus.resource_requested_statuses()
        )
        async with self._db.begin_session_read_committed() as session:
            rows = (
                (
                    await session.execute(
                        sa.select(KernelRow).where(
                            KernelRow.agent == agent_id,
                            KernelRow.status.in_(active_statuses),
                        )
                    )
                )
                .scalars()
                .all()
            )
            kernels = [row.to_kernel_info() for row in rows]
            if kernels and not force:
                distinct_sessions = len({kernel.session.session_id for kernel in kernels})
                raise AgentHasConflictingSessions(agent_id, distinct_sessions)

            await session.execute(
                sa.update(agents)
                .where(agents.c.id == agent_id)
                .values(
                    resource_group_id=resource_group_id,
                    scaling_group=sa.select(ScalingGroupRow.name)
                    .where(ScalingGroupRow.id == resource_group_id)
                    .scalar_subquery(),
                )
            )
        return kernels

    async def search_agents(
        self,
        querier: BatchQuerier,
    ) -> AgentListResult:
        """Searches agents with total count."""

        async with self._db.begin_readonly_session() as db_sess:
            query = sa.select(AgentRow).options(
                selectinload(AgentRow.agent_resource_rows).joinedload(
                    AgentResourceRow.slot_type_row
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

    async def upsert_agent_resource_capacity(
        self,
        bulk_upserter: BulkUpserter[AgentResourceRow],
    ) -> int:
        """Bulk UPSERT agent resource capacity rows.

        On INSERT: sets capacity (used defaults to 0).
        On CONFLICT: updates capacity only.

        Returns:
            Number of rows upserted.
        """
        async with self._db.begin_session_read_committed() as db_sess:
            result = await execute_bulk_upserter(
                db_sess,
                bulk_upserter,
                index_elements=["agent_id", "slot_name"],
            )
            return result.upserted_count
