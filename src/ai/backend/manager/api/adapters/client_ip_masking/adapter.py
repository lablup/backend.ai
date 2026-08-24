"""Client IP masking adapter bridging DTOs and Processors."""

from __future__ import annotations

from ai.backend.common.data.entity.client_ip_masking import ClientIPMaskingPolicyID
from ai.backend.common.dto.manager.v2.client_ip_masking.request import (
    AdminSearchClientIPMaskingPoliciesInput,
    AdminUpsertClientIPMaskingPolicyInput,
    ClientIPMaskingPolicyFilter,
    ClientIPMaskingPolicyOrder,
)
from ai.backend.common.dto.manager.v2.client_ip_masking.response import (
    AdminSearchClientIPMaskingPoliciesPayload,
    ClientIPMaskingPolicyNode,
    ClientIPMaskingPolicyPayload,
)
from ai.backend.common.dto.manager.v2.client_ip_masking.types import (
    ClientIPMaskingMode as ClientIPMaskingModeDTO,
)
from ai.backend.common.dto.manager.v2.client_ip_masking.types import (
    ClientIPMaskingPolicyOrderField,
)
from ai.backend.common.dto.manager.v2.client_ip_masking.types import (
    ClientIPMaskingTarget as ClientIPMaskingTargetDTO,
)
from ai.backend.common.dto.manager.v2.common import OrderDirection
from ai.backend.manager.api.adapter_options.pagination.pagination import PaginationSpec
from ai.backend.manager.api.adapters.base import BaseAdapter
from ai.backend.manager.data.client_ip.masking import ClientIPMaskingMode, ClientIPMaskingTarget
from ai.backend.manager.data.client_ip.types import ClientIPMaskingPolicyData
from ai.backend.manager.models.clauses import QueryCondition, QueryOrder
from ai.backend.manager.models.client_ip_masking.conditions import ClientIPMaskingPolicyConditions
from ai.backend.manager.models.client_ip_masking.orders import ClientIPMaskingPolicyOrders
from ai.backend.manager.models.client_ip_masking.row import ClientIPMaskingPolicyRow
from ai.backend.manager.models.client_ip_masking.searchers import ClientIPMaskingPolicySearcher
from ai.backend.manager.services.client_ip_masking.actions.purge import (
    PurgeClientIPMaskingPolicyAction,
)
from ai.backend.manager.services.client_ip_masking.actions.search import (
    SearchClientIPMaskingPoliciesAction,
)
from ai.backend.manager.services.client_ip_masking.actions.upsert import (
    UpsertClientIPMaskingPolicyAction,
)


def _pagination_spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=ClientIPMaskingPolicyOrders.target_type(ascending=True),
        backward_order=ClientIPMaskingPolicyOrders.target_type(ascending=False),
        forward_condition_factory=ClientIPMaskingPolicyConditions.by_cursor_forward,
        backward_condition_factory=ClientIPMaskingPolicyConditions.by_cursor_backward,
        tiebreaker_order=ClientIPMaskingPolicyRow.id.asc(),
    )


class ClientIPMaskingAdapter(BaseAdapter):
    """Adapter for the client IP masking policies."""

    async def admin_search(
        self, input: AdminSearchClientIPMaskingPoliciesInput
    ) -> AdminSearchClientIPMaskingPoliciesPayload:
        conditions = self._convert_filter(input.filter) if input.filter else []
        orders = self._convert_orders(input.order) if input.order else []
        searcher = self._build_searcher(
            ClientIPMaskingPolicySearcher,
            conditions=conditions,
            orders=orders,
            pagination_spec=_pagination_spec(),
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )
        result = await self._processors.client_ip_masking.global_search.run(
            SearchClientIPMaskingPoliciesAction(searcher=searcher)
        )
        return AdminSearchClientIPMaskingPoliciesPayload(
            items=[self._data_to_node(item) for item in result.items],
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def admin_upsert(
        self, input: AdminUpsertClientIPMaskingPolicyInput
    ) -> ClientIPMaskingPolicyPayload:
        result = await self._processors.client_ip_masking.global_upsert.run(
            UpsertClientIPMaskingPolicyAction(
                target_type=ClientIPMaskingTarget(input.target_type.value),
                mode=ClientIPMaskingMode(input.mode.value),
                ipv4_prefix=input.ipv4_prefix,
                ipv6_prefix=input.ipv6_prefix,
            )
        )
        return ClientIPMaskingPolicyPayload(policy=self._data_to_node(result.data))

    async def admin_purge(self, policy_id: ClientIPMaskingPolicyID) -> ClientIPMaskingPolicyPayload:
        result = await self._processors.client_ip_masking.purge.run(
            PurgeClientIPMaskingPolicyAction(id=policy_id)
        )
        return ClientIPMaskingPolicyPayload(policy=self._data_to_node(result.data))

    @staticmethod
    def _convert_filter(f: ClientIPMaskingPolicyFilter) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []
        if f.target_type is not None:
            conditions.append(
                ClientIPMaskingPolicyConditions.by_target_type(
                    ClientIPMaskingTarget(f.target_type.value)
                )
            )
        if f.mode is not None:
            conditions.append(
                ClientIPMaskingPolicyConditions.by_mode(ClientIPMaskingMode(f.mode.value))
            )
        return conditions

    @staticmethod
    def _convert_orders(orders: list[ClientIPMaskingPolicyOrder]) -> list[QueryOrder]:
        result: list[QueryOrder] = []
        for o in orders:
            ascending = o.direction == OrderDirection.ASC
            match o.field:
                case ClientIPMaskingPolicyOrderField.TARGET_TYPE:
                    result.append(ClientIPMaskingPolicyOrders.target_type(ascending))
                case ClientIPMaskingPolicyOrderField.MODE:
                    result.append(ClientIPMaskingPolicyOrders.mode(ascending))
                case ClientIPMaskingPolicyOrderField.CREATED_AT:
                    result.append(ClientIPMaskingPolicyOrders.created_at(ascending))
                case ClientIPMaskingPolicyOrderField.UPDATED_AT:
                    result.append(ClientIPMaskingPolicyOrders.updated_at(ascending))
        return result

    @staticmethod
    def _data_to_node(data: ClientIPMaskingPolicyData) -> ClientIPMaskingPolicyNode:
        return ClientIPMaskingPolicyNode(
            id=data.id,
            target_type=ClientIPMaskingTargetDTO(data.target_type.value),
            mode=ClientIPMaskingModeDTO(data.mode.value),
            ipv4_prefix=data.ipv4_prefix,
            ipv6_prefix=data.ipv6_prefix,
            created_at=data.created_at,
            updated_at=data.updated_at,
        )
