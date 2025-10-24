import logging
from typing import TYPE_CHECKING, Any, Optional, override

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import selectinload
from sqlalchemy.sql import Select

from ai.backend.common.exception import AgentNotFound
from ai.backend.common.types import AgentId, ImageID
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.data.agent.modifier import AgentStatusModifier
from ai.backend.manager.data.agent.types import (
    AgentData,
    AgentHeartbeatUpsert,
    AgentOrderField,
    AgentStatus,
    UpsertResult,
)
from ai.backend.manager.data.image.types import ImageDataWithDetails
from ai.backend.manager.errors.resource import ScalingGroupNotFound
from ai.backend.manager.models import agents
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.scaling_group import ScalingGroupRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.agent.types import AgentFilterOptions, AgentOrderingOptions
from ai.backend.manager.repositories.types import (
    BaseFilterApplier,
    BaseOrderingApplier,
    GenericQueryBuilder,
    PaginationOptions,
)
from ai.backend.manager.types import OffsetBasedPaginationOptions

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class AgentFilterApplier(BaseFilterApplier[AgentFilterOptions]):
    """Applies agent-specific filters to SQL queries."""

    @override
    def apply_entity_filters(
        self, stmt: Select, filters: AgentFilterOptions
    ) -> tuple[list[Any], Select]:
        """Apply AgentFilterOptions to SQL statement and return conditions."""
        conditions = []

        # Apply field-specific filters with StringFilter support
        if filters.id is not None:
            id_condition = filters.id.apply_to_column(AgentRow.id)
            if id_condition is not None:
                conditions.append(id_condition)

        if filters.status is not None:
            from ai.backend.manager.repositories.agent.types import AgentStatusFilterType

            if filters.status.type == AgentStatusFilterType.EQUALS:
                conditions.append(AgentRow.status == filters.status.values[0])
            elif filters.status.type == AgentStatusFilterType.IN:
                conditions.append(AgentRow.status.in_(filters.status.values))

        if filters.region is not None:
            region_condition = filters.region.apply_to_column(AgentRow.region)
            if region_condition is not None:
                conditions.append(region_condition)

        if filters.scaling_group is not None:
            sg_condition = filters.scaling_group.apply_to_column(AgentRow.scaling_group)
            if sg_condition is not None:
                conditions.append(sg_condition)

        if filters.schedulable is not None:
            conditions.append(AgentRow.schedulable == filters.schedulable)

        if filters.addr is not None:
            addr_condition = filters.addr.apply_to_column(AgentRow.addr)
            if addr_condition is not None:
                conditions.append(addr_condition)

        if filters.version is not None:
            version_condition = filters.version.apply_to_column(AgentRow.version)
            if version_condition is not None:
                conditions.append(version_condition)

        # Handle logical operations (AND/OR/NOT)
        if filters.AND is not None:
            for sub_filter in filters.AND:
                sub_conditions, stmt = self.apply_entity_filters(stmt, sub_filter)
                conditions.extend(sub_conditions)
        if filters.OR is not None:
            or_conditions = []
            for sub_filter in filters.OR:
                sub_conditions, stmt = self.apply_entity_filters(stmt, sub_filter)
                if sub_conditions:
                    or_conditions.append(sa.and_(*sub_conditions))
            if or_conditions:
                conditions.append(sa.or_(*or_conditions))
        if filters.NOT is not None:
            for sub_filter in filters.NOT:
                sub_conditions, stmt = self.apply_entity_filters(stmt, sub_filter)
                if sub_conditions:
                    conditions.append(sa.not_(sa.and_(*sub_conditions)))

        return conditions, stmt


class AgentOrderingApplier(BaseOrderingApplier[AgentOrderingOptions]):
    """Applies agent-specific ordering to SQL queries."""

    @override
    def get_order_column(self, field: Any) -> sa.Column:
        """Get the SQLAlchemy column for the given agent order field."""
        # Map AgentOrderField to AgentRow columns
        if isinstance(field, AgentOrderField):
            # Enum value now matches DB column name directly
            column_name = field.value
        else:
            # If it's a tuple, extract the field
            column_name = field[0].value if isinstance(field, tuple) else str(field)
        return getattr(AgentRow, column_name, AgentRow.id)


class AgentModelConverter:
    """Converts AgentRow to AgentData"""

    def convert_to_data(self, model: AgentRow) -> AgentData:
        """Convert AgentRow instance to AgentData"""
        return model.to_data()


class AgentDBSource:
    """Database source for agent-related operations."""

    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    async def fetch_agent_ids_by_condition(
        self,
        filter_options: Optional[AgentFilterOptions],
        ordering_options: AgentOrderingOptions,
        limit: Optional[int],
        offset: Optional[int],
        scaling_group: Optional[str],
        status_list: list[AgentStatus],
    ) -> list[AgentId]:
        from ai.backend.manager.api.gql.base import StringFilter
        from ai.backend.manager.repositories.agent.types import (
            AgentStatusFilter,
            AgentStatusFilterType,
        )

        # Build combined filter options with scaling_group and status_list
        combined_filter = filter_options or AgentFilterOptions()

        # Create additional filters for scaling_group and status_list
        if scaling_group is not None:
            # Merge with existing scaling_group filter or create new one
            if combined_filter.scaling_group is None:
                combined_filter.scaling_group = StringFilter(equals=scaling_group)
        if len(status_list) > 0:
            # Merge with existing status filter or create new one
            if combined_filter.status is None:
                combined_filter.status = AgentStatusFilter(
                    type=AgentStatusFilterType.IN, values=status_list
                )

        # Create pagination options
        pagination = PaginationOptions(
            offset=OffsetBasedPaginationOptions(offset=offset or 0, limit=limit)
        )

        # Initialize the generic query builder with agent-specific components
        agent_query_builder = GenericQueryBuilder[
            AgentRow, AgentData, AgentFilterOptions, AgentOrderingOptions
        ](
            model_class=AgentRow,
            filter_applier=AgentFilterApplier(),
            ordering_applier=AgentOrderingApplier(),
            model_converter=AgentModelConverter(),
            cursor_type_name="Agent",
        )

        # Build query using the generic query builder
        querybuild_result = agent_query_builder.build_pagination_queries(
            pagination=pagination,
            ordering=ordering_options,
            filters=combined_filter,
        )

        async with self._db.begin_readonly_session() as db_session:
            result = await db_session.scalars(querybuild_result.data_query)
            agent_rows = result.all()
            agent_ids: list[AgentId] = [AgentId(row.id) for row in agent_rows]
            return agent_ids

    async def get_images_by_digest(self, digests: list[str]) -> dict[ImageID, ImageDataWithDetails]:
        async with self._db.begin_readonly_session() as db_session:
            query = (
                sa.select(ImageRow)
                .where(ImageRow.config_digest.in_(digests))
                .options(selectinload(ImageRow.aliases))
            )
            results: list[ImageRow] = (await db_session.scalars(query)).all()
            images_data: dict[ImageID, ImageDataWithDetails] = {}
            for image_row in results:
                images_data[ImageID(image_row.id)] = image_row.to_detailed_dataclass()
            return images_data

    async def get_by_id(self, agent_id: AgentId) -> AgentData:
        async with self._db.begin_readonly_session() as db_session:
            agent_row: Optional[AgentRow] = await db_session.scalar(
                sa.select(AgentRow).where(AgentRow.id == agent_id)
            )
            if agent_row is None:
                log.error(f"Agent with id {agent_id} not found")
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
            row: Optional[AgentRow] = await session.scalar(query)
            agent_data = row.to_heartbeat_update_data() if row is not None else None
            upsert_result = UpsertResult.from_state_comparison(agent_data, upsert_data)

            stmt = pg_insert(agents).values(upsert_data.insert_fields)
            final_query = stmt.on_conflict_do_update(
                index_elements=["id"], set_=upsert_data.update_fields
            )

            await session.execute(final_query)

            return upsert_result

    async def update_agent_status_exit(
        self, agent_id: AgentId, modifier: AgentStatusModifier
    ) -> None:
        async with self._db.begin_session() as session:
            fetch_query = (
                sa.select(AgentRow.status)
                .select_from(AgentRow)
                .where(AgentRow.id == agent_id)
                .with_for_update()
            )
            prev_status = await session.scalar(fetch_query)
            if prev_status in (None, AgentStatus.LOST, AgentStatus.TERMINATED):
                return

            if modifier.status == AgentStatus.LOST:
                log.warning("agent {0} heartbeat timeout detected.", agent_id)
            elif modifier.status == AgentStatus.TERMINATED:
                log.info("agent {0} has terminated.", agent_id)

            update_query = (
                sa.update(AgentRow)
                .values(modifier.fields_to_update())
                .where(AgentRow.id == agent_id)
            )
            await session.execute(update_query)

    async def update_agent_status(self, agent_id: AgentId, modifier: AgentStatusModifier) -> None:
        async with self._db.begin_session() as session:
            query = (
                sa.update(AgentRow)
                .values(modifier.fields_to_update())
                .where(AgentRow.id == agent_id)
            )
            await session.execute(query)
