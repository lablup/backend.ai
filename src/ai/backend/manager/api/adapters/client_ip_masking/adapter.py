"""Client IP masking adapter bridging DTOs and Processors."""

from __future__ import annotations

from typing import assert_never

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
from ai.backend.manager.models.client_ip_masking.row import ClientIPMaskingPolicyRow
from ai.backend.manager.models.client_ip_masking.searchable_fields import (
    ClientIPMaskingPolicySearchableFields,
)
from ai.backend.manager.models.client_ip_masking.searchers import ClientIPMaskingPolicySearcher
from ai.backend.manager.models.specs.searcher import GlobalSearcher
from ai.backend.manager.services.client_ip_masking.actions.purge import (
    PurgeClientIPMaskingPolicyAction,
)
from ai.backend.manager.services.client_ip_masking.actions.search import (
    SearchClientIPMaskingPoliciesAction,
)
from ai.backend.manager.services.client_ip_masking.actions.upsert import (
    UpsertClientIPMaskingPolicyAction,
)
from ai.backend.manager.services.client_ip_masking.processors import ClientIPMaskingProcessors


def _pagination_spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=ClientIPMaskingPolicySearchableFields.own.target_type.order.apply(
            ascending=True
        ),
        cursor_column=ClientIPMaskingPolicyRow.id,
    )


class ClientIPMaskingAdapter(BaseAdapter):
    """Adapter for the client IP masking policies."""

    _client_ip_masking: ClientIPMaskingProcessors

    def __init__(self, client_ip_masking: ClientIPMaskingProcessors) -> None:
        self._client_ip_masking = client_ip_masking

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
        result = await self._client_ip_masking.global_search.run(
            SearchClientIPMaskingPoliciesAction(
                searcher=GlobalSearcher(used_by=(), searcher=searcher)
            )
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
        result = await self._client_ip_masking.global_upsert.run(
            UpsertClientIPMaskingPolicyAction(
                target_type=ClientIPMaskingTarget(input.target_type.value),
                mode=ClientIPMaskingMode(input.mode.value),
                ipv4_prefix=input.ipv4_prefix,
                ipv6_prefix=input.ipv6_prefix,
            )
        )
        return ClientIPMaskingPolicyPayload(policy=self._data_to_node(result.data))

    async def admin_purge(self, policy_id: ClientIPMaskingPolicyID) -> ClientIPMaskingPolicyPayload:
        result = await self._client_ip_masking.purge.run(
            PurgeClientIPMaskingPolicyAction(id=policy_id)
        )
        return ClientIPMaskingPolicyPayload(policy=self._data_to_node(result.data))

    @staticmethod
    def _convert_filter(f: ClientIPMaskingPolicyFilter) -> list[QueryCondition]:
        fields = ClientIPMaskingPolicySearchableFields.own
        conditions: list[QueryCondition] = []
        if f.target_type is not None:
            conditions.append(
                fields.target_type.filter.equals(ClientIPMaskingTarget(f.target_type.value))
            )
        if f.mode is not None:
            conditions.append(fields.mode.filter.equals(ClientIPMaskingMode(f.mode.value)))
        return conditions

    @staticmethod
    def _convert_orders(orders: list[ClientIPMaskingPolicyOrder]) -> list[QueryOrder]:
        fields = ClientIPMaskingPolicySearchableFields.own
        result: list[QueryOrder] = []
        for o in orders:
            ascending = o.direction == OrderDirection.ASC
            match o.field:
                case ClientIPMaskingPolicyOrderField.TARGET_TYPE:
                    result.append(fields.target_type.order.apply(ascending))
                case ClientIPMaskingPolicyOrderField.MODE:
                    result.append(fields.mode.order.apply(ascending))
                case ClientIPMaskingPolicyOrderField.CREATED_AT:
                    result.append(fields.created_at.order.apply(ascending))
                case ClientIPMaskingPolicyOrderField.UPDATED_AT:
                    result.append(fields.updated_at.order.apply(ascending))
                case _:
                    assert_never(o.field)
        return result

    @staticmethod
    def _data_to_node(data: ClientIPMaskingPolicyData) -> ClientIPMaskingPolicyNode:
        return ClientIPMaskingPolicyNode(
            id=data.id,
            entity_id=data.entity_id(),
            target_type=ClientIPMaskingTargetDTO(data.target_type.value),
            mode=ClientIPMaskingModeDTO(data.mode.value),
            ipv4_prefix=data.ipv4_prefix,
            ipv6_prefix=data.ipv6_prefix,
            created_at=data.created_at,
            updated_at=data.updated_at,
        )
