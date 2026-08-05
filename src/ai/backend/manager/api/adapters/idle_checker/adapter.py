"""Idle checker adapter bridging DTOs and Processors."""

from __future__ import annotations

from collections.abc import Sequence
from functools import lru_cache
from typing import cast

from ai.backend.common.api_handlers import SENTINEL
from ai.backend.common.data.idle_checker.types import (
    CheckerType,
    IdleCheckerSpec,
    MetricLabel,
    NetworkTimeoutSpec,
    SessionLifetimeSpec,
    UtilizationSpec,
    UtilizationThresholdEntry,
)
from ai.backend.common.dto.manager.v2.common import OrderDirection
from ai.backend.common.dto.manager.v2.idle_checker.request import (
    CreateIdleCheckerInput,
    IdleCheckerFilter,
    IdleCheckerOrder,
    IdleCheckerSpecInputDTO,
    PurgeIdleCheckerInput,
    SearchIdleCheckersInput,
    UpdateIdleCheckerInput,
    UtilizationSpecInputDTO,
)
from ai.backend.common.dto.manager.v2.idle_checker.response import (
    CreateIdleCheckerPayload,
    IdleCheckerNode,
    IdleCheckerSpecInfo,
    NetworkTimeoutSpecInfo,
    PurgeIdleCheckerPayload,
    SearchIdleCheckerPayload,
    SessionLifetimeSpecInfo,
    UpdateIdleCheckerPayload,
    UtilizationSpecInfo,
    UtilizationThresholdInfo,
)
from ai.backend.common.dto.manager.v2.idle_checker.types import (
    IdleCheckerOrderField,
    IdleCheckerTypeDTO,
)
from ai.backend.common.dto.manager.v2.prometheus_query_preset.types import MetricLabelEntryInfo
from ai.backend.common.identifier.idle_checker import IdleCheckerID
from ai.backend.manager.api.adapter_options.pagination.pagination import PaginationSpec
from ai.backend.manager.api.adapters.base import BaseAdapter
from ai.backend.manager.data.idle_checker.types import IdleCheckerData
from ai.backend.manager.models.clauses import QueryCondition, QueryOrder
from ai.backend.manager.models.idle_checker.conditions import IdleCheckerConditions
from ai.backend.manager.models.idle_checker.orders import IdleCheckerOrders
from ai.backend.manager.models.idle_checker.row import IdleCheckerRow
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    Creator,
    NoPagination,
    Purger,
    Updater,
    combine_conditions_or,
    negate_conditions,
)
from ai.backend.manager.repositories.idle_checker.creators import IdleCheckerCreatorSpec
from ai.backend.manager.repositories.idle_checker.purgers import IdleCheckerPurgerSpec
from ai.backend.manager.repositories.idle_checker.updaters import IdleCheckerUpdaterSpec
from ai.backend.manager.services.idle_checker.actions.admin_search import (
    AdminSearchIdleCheckersAction,
)
from ai.backend.manager.services.idle_checker.actions.create import CreateIdleCheckerAction
from ai.backend.manager.services.idle_checker.actions.purge import PurgeIdleCheckerAction
from ai.backend.manager.services.idle_checker.actions.update import UpdateIdleCheckerAction
from ai.backend.manager.types import OptionalState, TriState


@lru_cache(maxsize=1)
def _get_idle_checker_pagination_spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=IdleCheckerOrders.created_at(ascending=False),
        backward_order=IdleCheckerOrders.created_at(ascending=True),
        forward_condition_factory=IdleCheckerConditions.by_cursor_forward,
        backward_condition_factory=IdleCheckerConditions.by_cursor_backward,
        tiebreaker_order=IdleCheckerOrders.id(ascending=True),
    )


class IdleCheckerAdapter(BaseAdapter):
    """Adapter for global idle checker operations (admin-only)."""

    async def admin_create(
        self,
        input: CreateIdleCheckerInput,
    ) -> CreateIdleCheckerPayload:
        creator = Creator(
            spec=IdleCheckerCreatorSpec(
                name=input.name,
                description=input.description,
                target_session_types=input.target_session_types,
                initial_grace_period_seconds=input.initial_grace_period_seconds,
                spec=self._build_spec(input.checker_spec),
            )
        )
        action_result = await self._processors.idle_checker.create.wait_for_complete(
            CreateIdleCheckerAction(creator=creator)
        )
        return CreateIdleCheckerPayload(
            idle_checker=self._data_to_node(action_result.idle_checker),
        )

    async def batch_load_by_ids(
        self,
        ids: Sequence[IdleCheckerID],
    ) -> list[IdleCheckerNode | None]:
        """Return nodes in input order, with None for missing IDs."""

        if not ids:
            return []
        querier = BatchQuerier(
            pagination=NoPagination(),
            conditions=[IdleCheckerConditions.by_ids(ids)],
        )
        action_result = await self._processors.idle_checker.admin_search.wait_for_complete(
            AdminSearchIdleCheckersAction(querier=querier)
        )
        node_map = {node.id: node for node in map(self._data_to_node, action_result.items)}
        return [node_map.get(checker_id) for checker_id in ids]

    async def admin_search(self, input: SearchIdleCheckersInput) -> SearchIdleCheckerPayload:
        conditions = self._convert_filter(input.filter) if input.filter else []
        orders = self._convert_orders(input.order) if input.order else []
        querier = self._build_querier(
            conditions=conditions,
            orders=orders,
            pagination_spec=_get_idle_checker_pagination_spec(),
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )
        action_result = await self._processors.idle_checker.admin_search.wait_for_complete(
            AdminSearchIdleCheckersAction(querier=querier)
        )
        return SearchIdleCheckerPayload(
            items=[self._data_to_node(item) for item in action_result.items],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    async def admin_update(
        self,
        input: UpdateIdleCheckerInput,
    ) -> UpdateIdleCheckerPayload:
        updater: Updater[IdleCheckerRow] = Updater(
            spec=IdleCheckerUpdaterSpec(
                name=OptionalState.from_nullable(input.name),
                description=(
                    TriState.nop()
                    if input.description is SENTINEL
                    else TriState.nullify()
                    if input.description is None
                    else TriState.update(input.description)
                ),
                target_session_types=OptionalState.from_nullable(input.target_session_types),
                initial_grace_period_seconds=OptionalState.from_nullable(
                    input.initial_grace_period_seconds
                ),
                spec=self._build_spec_update(input.checker_spec),
            ),
            pk_value=input.id,
        )
        action_result = await self._processors.idle_checker.update.wait_for_complete(
            UpdateIdleCheckerAction(updater=updater)
        )
        return UpdateIdleCheckerPayload(
            idle_checker=self._data_to_node(action_result.idle_checker),
        )

    async def admin_purge(
        self,
        input: PurgeIdleCheckerInput,
    ) -> PurgeIdleCheckerPayload:
        purger = Purger(spec=IdleCheckerPurgerSpec(checker_id=input.id))
        action_result = await self._processors.idle_checker.purge.wait_for_complete(
            PurgeIdleCheckerAction(purger=purger)
        )
        return PurgeIdleCheckerPayload(id=action_result.idle_checker.id)

    @staticmethod
    def _data_to_node(data: IdleCheckerData) -> IdleCheckerNode:
        return IdleCheckerNode(
            id=data.id,
            name=data.name,
            description=data.description,
            checker_type=IdleCheckerTypeDTO(data.checker_type.value),
            target_session_types=data.target_session_types,
            initial_grace_period_seconds=data.initial_grace_period_seconds,
            spec=IdleCheckerAdapter._spec_to_info(data.spec),
            created_at=data.created_at,
            updated_at=data.updated_at,
        )

    @staticmethod
    def _spec_to_info(spec: IdleCheckerSpec) -> IdleCheckerSpecInfo:
        checker_type = IdleCheckerTypeDTO(spec.type.value)
        match spec.type:
            case CheckerType.SESSION_LIFETIME:
                session_lifetime = cast(SessionLifetimeSpec, spec.session_lifetime)
                return IdleCheckerSpecInfo(
                    type=checker_type,
                    session_lifetime=SessionLifetimeSpecInfo(
                        max_lifetime_seconds=session_lifetime.max_lifetime_seconds
                    ),
                )
            case CheckerType.NETWORK_TIMEOUT:
                network = cast(NetworkTimeoutSpec, spec.network)
                return IdleCheckerSpecInfo(
                    type=checker_type,
                    network=NetworkTimeoutSpecInfo(
                        max_network_inactivity_seconds=network.max_network_inactivity_seconds
                    ),
                )
            case CheckerType.UTILIZATION:
                utilization = cast(UtilizationSpec, spec.utilization)
                return IdleCheckerSpecInfo(
                    type=checker_type,
                    utilization=UtilizationSpecInfo(
                        max_underutilized_duration_seconds=(
                            utilization.max_underutilized_duration_seconds
                        ),
                        threshold=UtilizationThresholdInfo(
                            preset_id=utilization.threshold.preset_id,
                            threshold=utilization.threshold.threshold,
                            filter_labels=[
                                MetricLabelEntryInfo(key=label.key, value=label.value)
                                for label in utilization.threshold.filter_labels
                            ],
                            group_labels=utilization.threshold.group_labels,
                        ),
                    ),
                )

    @staticmethod
    def _build_spec(checker_spec: IdleCheckerSpecInputDTO) -> IdleCheckerSpec:
        if checker_spec.session_lifetime is not None:
            session_lifetime = checker_spec.session_lifetime
            return IdleCheckerSpec(
                type=CheckerType.SESSION_LIFETIME,
                session_lifetime=SessionLifetimeSpec(
                    max_lifetime_seconds=session_lifetime.max_lifetime_seconds
                ),
            )
        if checker_spec.network is not None:
            network = checker_spec.network
            return IdleCheckerSpec(
                type=CheckerType.NETWORK_TIMEOUT,
                network=NetworkTimeoutSpec(
                    max_network_inactivity_seconds=network.max_network_inactivity_seconds
                ),
            )
        utilization = cast(UtilizationSpecInputDTO, checker_spec.utilization)
        return IdleCheckerSpec(
            type=CheckerType.UTILIZATION,
            utilization=UtilizationSpec(
                max_underutilized_duration_seconds=(utilization.max_underutilized_duration_seconds),
                threshold=UtilizationThresholdEntry(
                    preset_id=utilization.threshold.preset_id,
                    threshold=utilization.threshold.threshold,
                    filter_labels=[
                        MetricLabel(key=entry.key, value=entry.value)
                        for entry in utilization.threshold.filter_labels
                    ],
                    group_labels=utilization.threshold.group_labels,
                ),
            ),
        )

    @classmethod
    def _build_spec_update(
        cls,
        checker_spec: IdleCheckerSpecInputDTO | None,
    ) -> OptionalState[IdleCheckerSpec]:
        if checker_spec is None:
            return OptionalState.nop()
        return OptionalState.update(cls._build_spec(checker_spec))

    def _convert_filter(self, filter_: IdleCheckerFilter) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []
        if filter_.name is not None:
            condition = self.convert_string_filter(
                filter_.name,
                contains_factory=IdleCheckerConditions.by_name_contains,
                equals_factory=IdleCheckerConditions.by_name_equals,
                starts_with_factory=IdleCheckerConditions.by_name_starts_with,
                ends_with_factory=IdleCheckerConditions.by_name_ends_with,
                in_factory=IdleCheckerConditions.by_name_in,
            )
            if condition is not None:
                conditions.append(condition)
        if filter_.checker_type is not None:
            if filter_.checker_type.equals is not None:
                conditions.append(
                    IdleCheckerConditions.by_checker_type_equals(
                        CheckerType(filter_.checker_type.equals.value)
                    )
                )
            if filter_.checker_type.in_ is not None:
                conditions.append(
                    IdleCheckerConditions.by_checker_type_in([
                        CheckerType(checker_type.value) for checker_type in filter_.checker_type.in_
                    ])
                )
        if filter_.created_at is not None:
            condition = filter_.created_at.build_query_condition(
                before_factory=IdleCheckerConditions.by_created_at_before,
                after_factory=IdleCheckerConditions.by_created_at_after,
                equals_factory=IdleCheckerConditions.by_created_at_equals,
            )
            if condition is not None:
                conditions.append(condition)
        if filter_.updated_at is not None:
            condition = filter_.updated_at.build_query_condition(
                before_factory=IdleCheckerConditions.by_updated_at_before,
                after_factory=IdleCheckerConditions.by_updated_at_after,
                equals_factory=IdleCheckerConditions.by_updated_at_equals,
            )
            if condition is not None:
                conditions.append(condition)
        if filter_.AND:
            for sub_filter in filter_.AND:
                conditions.extend(self._convert_filter(sub_filter))
        if filter_.OR:
            or_conditions: list[QueryCondition] = []
            for sub_filter in filter_.OR:
                or_conditions.extend(self._convert_filter(sub_filter))
            if or_conditions:
                conditions.append(combine_conditions_or(or_conditions))
        if filter_.NOT:
            not_conditions: list[QueryCondition] = []
            for sub_filter in filter_.NOT:
                not_conditions.extend(self._convert_filter(sub_filter))
            if not_conditions:
                conditions.append(negate_conditions(not_conditions))
        return conditions

    @staticmethod
    def _convert_orders(orders: list[IdleCheckerOrder]) -> list[QueryOrder]:
        result: list[QueryOrder] = []
        for order in orders:
            ascending = order.direction == OrderDirection.ASC
            match order.field:
                case IdleCheckerOrderField.NAME:
                    result.append(IdleCheckerOrders.name(ascending))
                case IdleCheckerOrderField.CHECKER_TYPE:
                    result.append(IdleCheckerOrders.checker_type(ascending))
                case IdleCheckerOrderField.CREATED_AT:
                    result.append(IdleCheckerOrders.created_at(ascending))
                case IdleCheckerOrderField.UPDATED_AT:
                    result.append(IdleCheckerOrders.updated_at(ascending))
        return result
