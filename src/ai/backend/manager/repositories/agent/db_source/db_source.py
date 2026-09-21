from __future__ import annotations

import logging
from collections.abc import Collection, Mapping, Sequence
from typing import TYPE_CHECKING, Any

import sqlalchemy as sa
from sqlalchemy.orm import selectinload

from ai.backend.common.data.entity.agent import AgentUUID
from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.common.types import AgentId, ImageID
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.data.agent.types import (
    AgentData,
    AgentHeartbeatUpsert,
    UpsertResult,
)
from ai.backend.manager.data.image.types import ImageDataWithDetails, ImageIdentifier
from ai.backend.manager.data.kernel.types import KernelInfo, KernelStatus
from ai.backend.manager.errors.agent import AgentHasConflictingSessions, AgentNotFound
from ai.backend.manager.errors.resource import ResourceGroupNotFound, UnresolvableResourceGroup
from ai.backend.manager.models.agent import AgentRow, agents
from ai.backend.manager.models.agent.searchable_fields import AgentSearchableFields
from ai.backend.manager.models.agent.upserters import AgentHeartbeatUpserter
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.resource_group import ResourceGroupRow
from ai.backend.manager.models.resource_slot import AgentResourceRow
from ai.backend.manager.models.resource_slot.upserters import AgentResourceUpserter
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.ops.v2.share.provider import ShareOpsProvider

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class AgentDBSource:
    """Database source for agent-related operations."""

    _db: ExtendedAsyncSAEngine
    _v2_ops: ShareOpsProvider

    def __init__(self, db: ExtendedAsyncSAEngine, v2_ops: ShareOpsProvider) -> None:
        self._db = db
        self._v2_ops = v2_ops

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

    async def agent_names_by_uuid(
        self, agent_uuids: Sequence[AgentUUID]
    ) -> Mapping[AgentUUID, AgentId]:
        """The name column of each named agent; an unknown uuid is absent."""
        if not agent_uuids:
            return {}
        async with self._db.begin_readonly_session_read_committed() as db_session:
            rows = (
                await db_session.execute(
                    sa.select(AgentRow.uuid, AgentRow.id).where(AgentRow.uuid.in_(agent_uuids))
                )
            ).all()
        return {AgentUUID(row[0]): AgentId(row[1]) for row in rows}

    async def get_by_id(self, agent_id: AgentId) -> AgentData:
        async with self._db.begin_readonly_session_read_committed() as db_session:
            agent_row: AgentRow | None = await db_session.scalar(
                sa.select(AgentRow).where(AgentRow.id == agent_id)
            )
            if agent_row is None:
                log.error("Agent with id {} not found", agent_id)
                raise AgentNotFound(f"Agent with id {agent_id} not found")
            return AgentSearchableFields.own.to_data(agent_row)

    async def upsert_agent_with_state(self, upsert_data: AgentHeartbeatUpsert) -> UpsertResult:
        async with self._db.begin_session_read_committed() as session:
            query = (
                sa.select(AgentRow)
                .where(AgentRow.id == upsert_data.metadata.id)
                .options(
                    selectinload(AgentRow.agent_resource_rows).joinedload(
                        AgentResourceRow.slot_type_row
                    )
                )
                .with_for_update()
            )
            row: AgentRow | None = await session.scalar(query)
            agent_data = row.to_heartbeat_update_data() if row is not None else None
            upsert_result = UpsertResult.from_state_comparison(agent_data, upsert_data)

            if row is not None:
                await session.execute(
                    sa.update(agents)
                    .where(agents.c.id == upsert_data.metadata.id)
                    .values(upsert_data.update_fields)
                )
                return upsert_result
            resource_group_id, resource_group_name = await self._resolve_resource_group(
                session, upsert_data.metadata.resource_group
            )
        # A concurrent registration inserting first is answered by the upsert's conflict key.
        async with self._v2_ops.write_ops() as w:
            await w.upsert_entity(
                AgentHeartbeatUpserter(
                    upsert_data=upsert_data,
                    resource_group_id=resource_group_id,
                    resource_group_name=resource_group_name,
                )
            )
        return upsert_result

    async def _resolve_resource_group(
        self, session: AsyncSession, resource_group_name: str | None
    ) -> tuple[ResourceGroupID, str]:
        """The group a new agent joins: the named one, else the default one."""
        group_filter: sa.ColumnElement[bool]
        group_order: sa.ColumnElement[Any]
        if resource_group_name is not None:
            group_filter = sa.or_(
                ResourceGroupRow.name == resource_group_name,
                ResourceGroupRow.is_default,
            )
            group_order = sa.case((ResourceGroupRow.name == resource_group_name, 0), else_=1)
        else:
            group_filter = ResourceGroupRow.is_default.is_(True)
            group_order = sa.asc(ResourceGroupRow.name)
        resolved = (
            await session.execute(
                sa.select(ResourceGroupRow.id, ResourceGroupRow.name)
                .where(group_filter)
                .order_by(group_order)
                .limit(1)
            )
        ).first()
        if resolved is None:
            if resource_group_name is not None:
                raise UnresolvableResourceGroup(
                    f"Scaling group '{resource_group_name}' not found "
                    "and no default scaling group is set."
                )
            raise UnresolvableResourceGroup(
                "No initial resource group name is configured and no default scaling group is set."
            )
        return ResourceGroupID(resolved.id), resolved.name

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
        their sessions. The lookup, the check, and the update run in one transaction; the
        agent's own and govern edges move to the new group after it.
        Raises ScalingGroupNotFound when no resource group matches
        ``resource_group_id``, and AgentNotFound when no agent row matches
        ``agent_id``.
        """
        active_statuses = (
            KernelStatus.resource_occupied_statuses() | KernelStatus.resource_requested_statuses()
        )
        async with self._db.begin_session_read_committed() as session:
            resource_group_name = await session.scalar(
                sa.select(ResourceGroupRow.name).where(ResourceGroupRow.id == resource_group_id)
            )
            if resource_group_name is None:
                raise ResourceGroupNotFound(str(resource_group_id))
            agent = (
                await session.execute(
                    sa.select(AgentRow.uuid, AgentRow.resource_group_id).where(
                        AgentRow.id == agent_id
                    )
                )
            ).first()
            if agent is None:
                raise AgentNotFound(f"Agent with id {agent_id} not found")

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
                    scaling_group=resource_group_name,
                )
            )
        if agent.resource_group_id != resource_group_id:
            async with self._v2_ops.write_ops() as w:
                await w.transfer(
                    [ResourceGroupID(agent.resource_group_id)],
                    [resource_group_id],
                    AgentUUID(agent.uuid),
                )
        return kernels

    async def sync_agent_resource_capacity(
        self,
        agent_id: AgentId,
        agent_uuid: AgentUUID,
        upserters: Sequence[AgentResourceUpserter],
        reported_slot_names: Collection[str],
    ) -> int:
        """UPSERT agent resource capacity rows and drop the slots the agent no
        longer reports.

        On INSERT: sets capacity (used defaults to 0).
        On CONFLICT: updates capacity only.
        Rows for unreported slots are deleted only when nothing holds them, so a
        slot that still carries an allocation survives until it is released.

        Returns:
            Number of rows upserted.
        """
        async with self._v2_ops.write_ops() as w:
            written = await w.atomic_upsert_field_entities(agent_uuid, upserters)
        async with self._db.begin_session_read_committed() as db_sess:
            await db_sess.execute(
                sa.delete(AgentResourceRow).where(
                    (AgentResourceRow.agent_id == str(agent_id))
                    & AgentResourceRow.slot_name.not_in(reported_slot_names)
                    & (AgentResourceRow.used == 0)
                    & (AgentResourceRow.reserved == 0)
                    & (AgentResourceRow.prereserved == 0)
                )
            )
        return len(written)
