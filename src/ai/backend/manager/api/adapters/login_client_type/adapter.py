"""Login client type adapter bridging DTOs and Processors."""

from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from ai.backend.common.data.entity.login_client_type import LoginClientTypeID
from ai.backend.common.dto.manager.defs import DEFAULT_PAGE_LIMIT
from ai.backend.common.dto.manager.v2.common import PartialBulkFailure, PartialBulkPayload
from ai.backend.common.dto.manager.v2.login_client_type.request import (
    CreateLoginClientTypeInput,
    LoginClientTypeFilter,
    LoginClientTypeOrder,
    PartialBulkPurgeLoginClientTypesInput,
    PartialBulkUpdateLoginClientTypesInput,
    SearchLoginClientTypesInput,
    UpdateLoginClientTypeInput,
)
from ai.backend.common.dto.manager.v2.login_client_type.response import (
    CreateLoginClientTypePayload,
    LoginClientTypeNode,
    PurgeLoginClientTypePayload,
    SearchLoginClientTypesPayload,
    UpdateLoginClientTypePayload,
)
from ai.backend.common.dto.manager.v2.login_client_type.types import (
    LoginClientTypeOrderField,
    OrderDirection,
)
from ai.backend.manager.actions.v2.bulk.result import PartialBulkResult
from ai.backend.manager.api.adapter_options.pagination.pagination import (
    PaginationOptions,
    PaginationSpec,
)
from ai.backend.manager.api.adapters.base import BaseAdapter
from ai.backend.manager.data.login_client_type.types import LoginClientTypeData
from ai.backend.manager.models.clauses import QueryCondition, QueryOrder
from ai.backend.manager.models.condition_utils import (
    combine_conditions_and,
    combine_conditions_or,
    negate_conditions,
)
from ai.backend.manager.models.login_client_type.creators import LoginClientTypeCreator
from ai.backend.manager.models.login_client_type.deprecated_search import (
    DeprecatedLoginClientTypeDescriptionConditions,
)
from ai.backend.manager.models.login_client_type.row import LoginClientTypeRow
from ai.backend.manager.models.login_client_type.scopes import PublicLoginClientTypeTarget
from ai.backend.manager.models.login_client_type.searchable_fields import (
    LoginClientTypeSearchableFields,
)
from ai.backend.manager.models.login_client_type.searchers import LoginClientTypeSearcher
from ai.backend.manager.models.login_client_type.updaters import LoginClientTypeUpdater
from ai.backend.manager.models.specs.searcher import ScopedSearcher
from ai.backend.manager.services.login_client_type.actions.bulk_get import (
    BulkGetLoginClientTypesAction,
)
from ai.backend.manager.services.login_client_type.actions.create import (
    CreateLoginClientTypeAction,
)
from ai.backend.manager.services.login_client_type.actions.get import (
    GetLoginClientTypeAction,
)
from ai.backend.manager.services.login_client_type.actions.partial_bulk_purge import (
    PartialBulkPurgeLoginClientTypesAction,
)
from ai.backend.manager.services.login_client_type.actions.partial_bulk_update import (
    PartialBulkUpdateLoginClientTypesAction,
)
from ai.backend.manager.services.login_client_type.actions.purge import (
    PurgeLoginClientTypeAction,
)
from ai.backend.manager.services.login_client_type.actions.scoped_search import (
    ScopedSearchLoginClientTypesAction,
)
from ai.backend.manager.services.login_client_type.actions.update import (
    UpdateLoginClientTypeAction,
)
from ai.backend.manager.services.login_client_type.processors import LoginClientTypeProcessors
from ai.backend.manager.types import OptionalState, TriState


def _pagination_spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=LoginClientTypeSearchableFields.own.created_at.order.apply(ascending=False),
        cursor_column=LoginClientTypeRow.id,
    )


class LoginClientTypeAdapter(BaseAdapter):
    """Adapter for login client type domain operations."""

    _login_client_type: LoginClientTypeProcessors

    def __init__(self, login_client_type: LoginClientTypeProcessors) -> None:
        self._login_client_type = login_client_type

    # --- Static helpers (grouped at top) ---

    @staticmethod
    def _data_to_node(data: LoginClientTypeData) -> LoginClientTypeNode:
        return LoginClientTypeNode(
            id=data.id,
            entity_id=data.entity_id(),
            name=data.name,
            description=data.description,
            created_at=data.created_at,
            modified_at=data.updated_at,
        )

    def _convert_orders(self, orders: list[LoginClientTypeOrder]) -> list[QueryOrder]:
        fields = LoginClientTypeSearchableFields.own
        result: list[QueryOrder] = []
        for order in orders:
            ascending = order.direction == OrderDirection.ASC
            match order.field:
                case LoginClientTypeOrderField.NAME:
                    result.append(fields.name.order.apply(ascending))
                case LoginClientTypeOrderField.CREATED_AT:
                    result.append(fields.created_at.order.apply(ascending))
                case LoginClientTypeOrderField.MODIFIED_AT:
                    result.append(fields.updated_at.order.apply(ascending))
        return result

    # --- Non-admin methods ---

    async def get(self, type_id: UUID) -> LoginClientTypeNode:
        action_result = await self._login_client_type.get.run(
            GetLoginClientTypeAction(id=LoginClientTypeID(type_id))
        )
        return self._data_to_node(action_result.data)

    async def batch_load_by_ids(
        self, ids: Sequence[LoginClientTypeID]
    ) -> list[LoginClientTypeNode | Exception | None]:
        """Batch load login client types by id for DataLoader use, one answer per id."""
        if not ids:
            return []
        result = await self._login_client_type.bulk_get.run(BulkGetLoginClientTypesAction(ids=ids))
        return [
            self._data_to_node(item.value)
            if item.value is not None
            else self.batch_load_failure(item.error)
            for item in result.items
        ]

    async def search(self, input: SearchLoginClientTypesInput) -> SearchLoginClientTypesPayload:
        """Search login client types, by cursor or by offset as the request names."""
        conditions = self._convert_filter(input.filter) if input.filter else []
        orders = self._convert_orders(input.order) if input.order else []
        options = PaginationOptions(
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )
        limit = input.limit
        if limit is None and not options.has_cursor:
            limit = DEFAULT_PAGE_LIMIT
        searcher = self._build_searcher(
            LoginClientTypeSearcher,
            conditions=conditions,
            orders=orders,
            pagination_spec=_pagination_spec(),
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=limit,
            offset=input.offset,
        )

        action_result = await self._login_client_type.scoped_search.run(
            ScopedSearchLoginClientTypesAction(
                searcher=ScopedSearcher(
                    scopes=[PublicLoginClientTypeTarget()], used_by=(), searcher=searcher
                )
            )
        )

        return SearchLoginClientTypesPayload(
            items=[self._data_to_node(item) for item in action_result.items],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    # --- Admin methods ---

    async def admin_create(self, input: CreateLoginClientTypeInput) -> CreateLoginClientTypePayload:
        creator = LoginClientTypeCreator(
            name=input.name,
            description=input.description,
        )
        action_result = await self._login_client_type.global_create.run(
            CreateLoginClientTypeAction(creator=creator)
        )
        return CreateLoginClientTypePayload(
            login_client_type=self._data_to_node(action_result.data),
        )

    # --- Write methods ---

    async def update(
        self, type_id: UUID, input: UpdateLoginClientTypeInput
    ) -> UpdateLoginClientTypePayload:
        """Update a login client type."""
        action_result = await self._login_client_type.update.run(
            UpdateLoginClientTypeAction(updater=self._to_updater(LoginClientTypeID(type_id), input))
        )
        return UpdateLoginClientTypePayload(
            login_client_type=self._data_to_node(action_result.data),
        )

    async def purge(self, type_id: UUID) -> PurgeLoginClientTypePayload:
        """Permanently remove a login client type."""
        action_result = await self._login_client_type.purge.run(
            PurgeLoginClientTypeAction(id=type_id)
        )
        return PurgeLoginClientTypePayload(id=action_result.data.id)

    async def partial_bulk_update(
        self, input: PartialBulkUpdateLoginClientTypesInput
    ) -> PartialBulkPayload[LoginClientTypeNode]:
        """Update several login client types, answering for each one."""
        result = await self._login_client_type.partial_bulk_update.run(
            PartialBulkUpdateLoginClientTypesAction(
                updaters=[
                    self._to_updater(LoginClientTypeID(item.id), item.input) for item in input.items
                ]
            )
        )
        return self._to_partial_bulk_payload(result)

    async def partial_bulk_purge(
        self, input: PartialBulkPurgeLoginClientTypesInput
    ) -> PartialBulkPayload[LoginClientTypeNode]:
        """Permanently remove several login client types, answering for each one."""
        result = await self._login_client_type.partial_bulk_purge.run(
            PartialBulkPurgeLoginClientTypesAction(
                ids=[LoginClientTypeID(type_id) for type_id in input.ids]
            )
        )
        return self._to_partial_bulk_payload(result)

    # --- Private helpers ---

    def _to_updater(
        self, type_id: LoginClientTypeID, input: UpdateLoginClientTypeInput
    ) -> LoginClientTypeUpdater:
        return LoginClientTypeUpdater(
            login_client_type_id=type_id,
            name=OptionalState.from_unset(input.name),
            description=TriState.from_unset(input.description),
        )

    def _to_partial_bulk_payload(
        self, result: PartialBulkResult[LoginClientTypeData]
    ) -> PartialBulkPayload[LoginClientTypeNode]:
        return PartialBulkPayload[LoginClientTypeNode](
            successes=[
                self._data_to_node(item.value) for item in result.items if item.value is not None
            ],
            failed=[
                PartialBulkFailure(id=item.entity_id, message=str(item.error))
                for item in result.items
                if item.error is not None
            ],
        )

    def _convert_filter(self, filter: LoginClientTypeFilter) -> list[QueryCondition]:
        fields = LoginClientTypeSearchableFields.own
        conditions: list[QueryCondition] = [
            *self.apply_uuid_filter(filter.entity_id, fields.id.filter),
            *self.apply_string_filter(filter.name, fields.name.filter),
            *self.apply_string_filter(
                filter.description, DeprecatedLoginClientTypeDescriptionConditions()
            ),
            *self.apply_datetime_filter(filter.created_at, fields.created_at.filter),
            *self.apply_datetime_filter(filter.modified_at, fields.updated_at.filter),
        ]

        if filter.AND:
            for sub_filter in filter.AND:
                conditions.extend(self._convert_filter(sub_filter))
        if filter.OR:
            or_conditions: list[QueryCondition] = []
            for sub_filter in filter.OR:
                sub_conditions = self._convert_filter(sub_filter)
                if sub_conditions:
                    or_conditions.append(combine_conditions_and(sub_conditions))
            if or_conditions:
                conditions.append(combine_conditions_or(or_conditions))
        if filter.NOT:
            for sub_filter in filter.NOT:
                sub_conditions = self._convert_filter(sub_filter)
                if sub_conditions:
                    conditions.append(negate_conditions(sub_conditions))

        return conditions
