import logging
import uuid
from datetime import datetime
from typing import Optional, Sequence
from uuid import UUID

import sqlalchemy as sa

from ai.backend.common.decorators import create_layer_aware_repository_decorator
from ai.backend.common.metrics.metric import LayerType
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.errors.resource import GroupNotFound
from ai.backend.manager.models.group import GroupRow, association_groups_users, groups
from ai.backend.manager.models.kernel import LIVE_STATUS, RESOURCE_USAGE_KERNEL_STATUSES, kernels
from ai.backend.manager.models.resource_usage import fetch_resource_usage
from ai.backend.manager.models.user import UserRole, users
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine, SASession
from ai.backend.manager.services.group.types import GroupCreator, GroupData, GroupModifier

# Layer-specific decorator for group repository
repository_decorator = create_layer_aware_repository_decorator(LayerType.GROUP)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class GroupRepository:
    _db: ExtendedAsyncSAEngine
    _config_provider: ManagerConfigProvider

    def __init__(
        self,
        db: ExtendedAsyncSAEngine,
        config_provider: ManagerConfigProvider,
    ) -> None:
        self._db = db
        self._config_provider = config_provider

    async def _get_group_by_id(self, session: SASession, group_id: uuid.UUID) -> GroupRow:
        """Private method to get a group by ID using an existing session.
        Raises GroupNotFound if not found."""
        result = await session.execute(sa.select(GroupRow).where(groups.c.id == group_id))
        group_row = result.scalar_one_or_none()
        if not group_row:
            raise GroupNotFound()
        return group_row

    @repository_decorator()
    async def create(self, creator: GroupCreator) -> GroupData:
        """Create a new group."""
        data = creator.fields_to_store()
        async with self._db.begin_session() as session:
            query = sa.insert(groups).values(data).returning(groups)
            result = await session.execute(query)
            row = result.first()
            group_data = GroupData.from_row(row)
            if group_data is None:
                raise GroupNotFound()
            return group_data

    @repository_decorator()
    async def modify_validated(
        self,
        group_id: uuid.UUID,
        modifier: GroupModifier,
        user_role: UserRole,
        user_update_mode: Optional[str] = None,
        user_uuids: Optional[list[uuid.UUID]] = None,
    ) -> Optional[GroupData]:
        """Modify a group with validation."""
        data = modifier.fields_to_update()

        if user_update_mode not in (None, "add", "remove"):
            raise ValueError("invalid user_update_mode")

        if not data and user_update_mode is None:
            return None

        async with self._db.begin_session() as session:
            # Handle user addition/removal
            if user_uuids and user_update_mode:
                if user_update_mode == "add":
                    values = [{"user_id": uuid, "group_id": group_id} for uuid in user_uuids]
                    await session.execute(
                        sa.insert(association_groups_users).values(values),
                    )
                elif user_update_mode == "remove":
                    await session.execute(
                        sa.delete(association_groups_users).where(
                            (association_groups_users.c.user_id.in_(user_uuids))
                            & (association_groups_users.c.group_id == group_id),
                        ),
                    )

            # Update group data if provided
            if data:
                result = await session.execute(
                    sa.update(groups).values(data).where(groups.c.id == group_id).returning(groups),
                )
                row = result.first()
                if row:
                    return GroupData.from_row(row)
                raise GroupNotFound()

            # If only user updates were performed, return None
            return None

    @repository_decorator()
    async def mark_inactive(self, group_id: uuid.UUID) -> bool:
        """Mark a group as inactive (soft delete)."""
        async with self._db.begin_session() as session:
            result = await session.execute(
                sa.update(groups)
                .values(
                    is_active=False,
                    integration_id=None,
                )
                .where(groups.c.id == group_id)
            )
            if result.rowcount > 0:
                return True
            raise GroupNotFound()

    @repository_decorator()
    async def get_container_stats_for_period(
        self,
        start_date: datetime,
        end_date: datetime,
        group_ids: Optional[Sequence[UUID]] = None,
    ) -> list[dict]:
        """Get container statistics for groups within a time period.
        Returns raw kernel data for statistics processing in service layer."""
        async with self._db.begin_readonly() as conn:
            j = kernels.join(groups, groups.c.id == kernels.c.group_id).join(
                users, users.c.uuid == kernels.c.user_uuid
            )
            query = (
                sa.select([
                    kernels.c.id,
                    kernels.c.container_id,
                    kernels.c.session_id,
                    kernels.c.session_name,
                    kernels.c.access_key,
                    kernels.c.agent,
                    kernels.c.domain_name,
                    kernels.c.group_id,
                    kernels.c.attached_devices,
                    kernels.c.occupied_slots,
                    kernels.c.resource_opts,
                    kernels.c.vfolder_mounts,
                    kernels.c.mounts,
                    kernels.c.image,
                    kernels.c.status,
                    kernels.c.status_info,
                    kernels.c.status_changed,
                    kernels.c.last_stat,
                    kernels.c.status_history,
                    kernels.c.created_at,
                    kernels.c.terminated_at,
                    kernels.c.cluster_mode,
                    groups.c.name,
                    users.c.email,
                    users.c.full_name,
                ])
                .select_from(j)
                .where(
                    # Filter sessions which existence period overlaps with requested period
                    (
                        (kernels.c.terminated_at >= start_date)
                        & (kernels.c.created_at < end_date)
                        & (kernels.c.status.in_(RESOURCE_USAGE_KERNEL_STATUSES))
                    )
                    |
                    # Or, filter running sessions which created before requested end_date
                    ((kernels.c.created_at < end_date) & (kernels.c.status.in_(LIVE_STATUS))),
                )
                .order_by(sa.asc(kernels.c.terminated_at))
            )
            if group_ids:
                query = query.where(kernels.c.group_id.in_(group_ids))
            result = await conn.execute(query)
            rows = result.fetchall()

        # Return raw data for statistics processing in service layer
        return [dict(row) for row in rows]

    @repository_decorator()
    async def fetch_project_resource_usage(
        self,
        start_date: datetime,
        end_date: datetime,
        project_ids: Optional[Sequence[UUID]] = None,
    ):
        """Fetch resource usage data for projects."""
        return await fetch_resource_usage(self._db, start_date, end_date, project_ids=project_ids)
