"""Session group adapter bridging DTOs and Processors."""

from __future__ import annotations

from collections.abc import Sequence
from typing import assert_never

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.session_group import SessionGroupID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.dto.manager.v2.common import OrderDirection
from ai.backend.common.dto.manager.v2.session_group.request import (
    AdminSearchSessionGroupsInput,
    PurgeSessionGroupInput,
    ScopedSearchSessionGroupsInput,
    SessionGroupFilter,
    SessionGroupOrder,
    UpdateSessionGroupInput,
)
from ai.backend.common.dto.manager.v2.session_group.response import (
    AdminSearchSessionGroupsPayload,
    PurgeSessionGroupPayload,
    SessionGroupNode,
    UpdateSessionGroupPayload,
)
from ai.backend.common.dto.manager.v2.session_group.types import (
    SessionGroupOrderField,
    SessionGroupPlacementDirectionEnum,
    SessionGroupPlacementEnforcementEnum,
)
from ai.backend.manager.actions.v2.ops.result import BatchOpsResult
from ai.backend.manager.api.adapter_options.pagination.pagination import PaginationSpec
from ai.backend.manager.api.adapters.base import BaseAdapter
from ai.backend.manager.data.session_group.types import (
    SessionGroupData,
    SessionGroupPlacementDirection,
    SessionGroupPlacementEnforcement,
)
from ai.backend.manager.models.clauses import QueryCondition, QueryOrder
from ai.backend.manager.models.condition_utils import (
    combine_conditions_and,
    combine_conditions_or,
    negate_conditions,
)
from ai.backend.manager.models.session_group.purgers import SessionGroupPurger
from ai.backend.manager.models.session_group.row import SessionGroupRow
from ai.backend.manager.models.session_group.scopes import (
    DomainSessionGroupTarget,
    ProjectSessionGroupTarget,
    UserSessionGroupTarget,
)
from ai.backend.manager.models.session_group.searchable_fields import SessionGroupSearchableFields
from ai.backend.manager.models.session_group.searchers import SessionGroupSearcher
from ai.backend.manager.models.session_group.updaters import SessionGroupUpdater
from ai.backend.manager.models.specs.searcher import GlobalSearcher, ScopedSearcher
from ai.backend.manager.services.session_group.actions.bulk_get import BulkGetSessionGroupsAction
from ai.backend.manager.services.session_group.actions.get import GetSessionGroupAction
from ai.backend.manager.services.session_group.actions.global_search import (
    GlobalSearchSessionGroupsAction,
)
from ai.backend.manager.services.session_group.actions.purge import PurgeSessionGroupAction
from ai.backend.manager.services.session_group.actions.scoped_search import (
    ScopedSearchSessionGroupsAction,
)
from ai.backend.manager.services.session_group.actions.update import UpdateSessionGroupAction
from ai.backend.manager.services.session_group.processors import SessionGroupProcessors
from ai.backend.manager.types import OptionalState

__all__ = ("SessionGroupAdapter",)

_SESSION_GROUP_PAGINATION_SPEC = PaginationSpec(
    forward_order=SessionGroupSearchableFields.own.created_at.order.apply(ascending=False),
    cursor_column=SessionGroupRow.id,
)


class SessionGroupAdapter(BaseAdapter):
    """Adapter for session group reads, placement policy updates and the purge."""

    _session_group: SessionGroupProcessors

    def __init__(self, session_group: SessionGroupProcessors) -> None:
        self._session_group = session_group

    async def bulk_get_ids(
        self, ids: Sequence[SessionGroupID]
    ) -> list[SessionGroupNode | Exception | None]:
        """Batch load session groups by id for DataLoader use."""
        if not ids:
            return []
        result = await self._session_group.bulk_get_ids.run(
            BulkGetSessionGroupsAction(ids=list(ids))
        )
        return [
            self._data_to_node(item.value)
            if item.value is not None
            else self.batch_load_failure(item.error)
            for item in result.items
        ]

    async def get(self, group_id: SessionGroupID) -> SessionGroupNode:
        """Retrieve a single session group by id."""
        result = await self._session_group.get.run(GetSessionGroupAction(group_id=group_id))
        return self._data_to_node(result.data)

    async def global_search(
        self, input: AdminSearchSessionGroupsInput
    ) -> AdminSearchSessionGroupsPayload:
        """Search every session group, deployment groups included (superadmin)."""
        searcher = self._build_searcher(
            SessionGroupSearcher,
            conditions=self._search_conditions(input.filter),
            orders=self._convert_orders(input.order) if input.order else [],
            pagination_spec=_SESSION_GROUP_PAGINATION_SPEC,
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )
        result = await self._session_group.global_search.run(
            GlobalSearchSessionGroupsAction(searcher=GlobalSearcher(used_by=(), searcher=searcher))
        )
        return self._to_payload(result)

    async def scoped_search(
        self, input: ScopedSearchSessionGroupsInput
    ) -> AdminSearchSessionGroupsPayload:
        """Search the session groups the named scopes reach, combined with OR."""
        searcher = self._build_searcher(
            SessionGroupSearcher,
            conditions=self._search_conditions(input.filter),
            orders=self._convert_orders(input.order) if input.order else [],
            pagination_spec=_SESSION_GROUP_PAGINATION_SPEC,
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )
        result = await self._session_group.scoped_search.run(
            ScopedSearchSessionGroupsAction(
                searcher=ScopedSearcher(
                    scopes=[
                        *(
                            DomainSessionGroupTarget(domain_id=DomainID(entry.value))
                            for entry in input.scope.domain or ()
                        ),
                        *(
                            ProjectSessionGroupTarget(project_id=ProjectID(entry.value))
                            for entry in input.scope.project or ()
                        ),
                        *(
                            UserSessionGroupTarget(user_id=UserID(entry.value))
                            for entry in input.scope.user or ()
                        ),
                    ],
                    used_by=(),
                    searcher=searcher,
                )
            )
        )
        return self._to_payload(result)

    async def purge(self, input: PurgeSessionGroupInput) -> PurgeSessionGroupPayload:
        """Remove a session group; its member sessions stay with their group cleared."""
        result = await self._session_group.purge.run(
            PurgeSessionGroupAction(purger=SessionGroupPurger(group_id=SessionGroupID(input.id)))
        )
        return PurgeSessionGroupPayload(entity_id=result.data.id)

    async def update(self, input: UpdateSessionGroupInput) -> UpdateSessionGroupPayload:
        """Change a session group's placement direction and enforcement."""
        updater = SessionGroupUpdater(
            group_id=SessionGroupID(input.id),
            placement_direction=(
                OptionalState.update(SessionGroupPlacementDirection(input.placement_direction))
                if isinstance(input.placement_direction, SessionGroupPlacementDirectionEnum)
                else OptionalState[SessionGroupPlacementDirection].nop()
            ),
            placement_enforcement=(
                OptionalState.update(SessionGroupPlacementEnforcement(input.placement_enforcement))
                if isinstance(input.placement_enforcement, SessionGroupPlacementEnforcementEnum)
                else OptionalState[SessionGroupPlacementEnforcement].nop()
            ),
        )
        result = await self._session_group.update.run(UpdateSessionGroupAction(updater=updater))
        return UpdateSessionGroupPayload(session_group=self._data_to_node(result.data))

    def _search_conditions(self, filter: SessionGroupFilter | None) -> list[QueryCondition]:
        """The filter's conditions; groups marked deleted are left out unless the top-level
        filter names ``deleted_at``."""
        if filter is None:
            return [SessionGroupSearchableFields.own.deleted_at.filter.is_null()]
        conditions = self._convert_filter(filter)
        if filter.deleted_at is None:
            conditions.append(SessionGroupSearchableFields.own.deleted_at.filter.is_null())
        return conditions

    def _convert_filter(self, filter: SessionGroupFilter) -> list[QueryCondition]:
        fields = SessionGroupSearchableFields.own
        conditions = [
            *self.apply_uuid_filter(filter.entity_id, fields.id.filter),
            *self.apply_uuid_filter(filter.domain_id, fields.domain_id.filter),
            *self.apply_uuid_filter(filter.project_id, fields.project_id.filter),
            *self.apply_uuid_filter(filter.owner_user_id, fields.owner_user_id.filter),
            *self.apply_enum_filter(filter.placement_direction, fields.placement_direction.filter),
            *self.apply_enum_filter(
                filter.placement_enforcement, fields.placement_enforcement.filter
            ),
            *self.apply_datetime_filter(filter.created_at, fields.created_at.filter),
            *self.apply_nullable_datetime_filter(filter.deleted_at, fields.deleted_at.filter),
        ]
        if filter.AND:
            for sub_filter in filter.AND:
                conditions.extend(self._convert_filter(sub_filter))
        if filter.OR:
            or_sub_conditions: list[QueryCondition] = []
            for sub_filter in filter.OR:
                sub_conditions = self._convert_filter(sub_filter)
                if sub_conditions:
                    or_sub_conditions.append(combine_conditions_and(sub_conditions))
            if or_sub_conditions:
                conditions.append(combine_conditions_or(or_sub_conditions))
        if filter.NOT:
            for sub_filter in filter.NOT:
                sub_conditions = self._convert_filter(sub_filter)
                if sub_conditions:
                    conditions.append(negate_conditions(sub_conditions))
        return conditions

    def _convert_orders(self, order: list[SessionGroupOrder]) -> list[QueryOrder]:
        return [self._convert_order(o) for o in order]

    def _convert_order(self, order: SessionGroupOrder) -> QueryOrder:
        """The query order one requested order field names."""
        fields = SessionGroupSearchableFields.own
        ascending = order.direction == OrderDirection.ASC
        match order.field:
            case SessionGroupOrderField.PLACEMENT_DIRECTION:
                return fields.placement_direction.order.apply(ascending)
            case SessionGroupOrderField.PLACEMENT_ENFORCEMENT:
                return fields.placement_enforcement.order.apply(ascending)
            case SessionGroupOrderField.CREATED_AT:
                return fields.created_at.order.apply(ascending)
            case SessionGroupOrderField.DELETED_AT:
                return fields.deleted_at.order.apply(ascending)
            case _:
                assert_never(order.field)

    def _to_payload(
        self, result: BatchOpsResult[SessionGroupData]
    ) -> AdminSearchSessionGroupsPayload:
        return AdminSearchSessionGroupsPayload(
            items=[self._data_to_node(item) for item in result.items],
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    @staticmethod
    def _data_to_node(data: SessionGroupData) -> SessionGroupNode:
        """Convert data layer type to Pydantic DTO."""
        return SessionGroupNode(
            id=data.id,
            entity_id=data.entity_id(),
            domain_id=data.domain_id,
            project_id=data.project_id,
            owner_user_id=data.owner_user_id,
            placement_direction=SessionGroupPlacementDirectionEnum(data.placement_direction),
            placement_enforcement=SessionGroupPlacementEnforcementEnum(data.placement_enforcement),
            created_at=data.created_at,
            deleted_at=data.deleted_at,
        )
