from __future__ import annotations

from collections.abc import Sequence

from ai.backend.common.contexts.user import current_user
from ai.backend.common.data.entity.entity_share import EntityShareID
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.types import EntityIdentifier, RuntimeEntityID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.dto.manager.v2.common import OrderDirection
from ai.backend.common.dto.manager.v2.entity_share.request import (
    CreateEntityShareInput,
    EntityShareFilter,
    EntityShareOrderBy,
    EntityShareScope,
    MySearchEntitySharesInput,
    ScopedSearchEntitySharesInput,
)
from ai.backend.common.dto.manager.v2.entity_share.response import (
    EntityShareNode,
    EntitySharePayload,
    SearchEntitySharesPayload,
)
from ai.backend.common.dto.manager.v2.entity_share.types import (
    EntityShareOrderField,
    EntityShareSideDTO,
    EntityShareStatusDTO,
)
from ai.backend.common.dto.manager.v2.rbac.types import PermissionBitDTO
from ai.backend.common.exception import UnreachableError
from ai.backend.manager.api.adapter_options.pagination.pagination import PaginationSpec
from ai.backend.manager.api.adapters.base import BaseAdapter
from ai.backend.manager.data.entity_share.types import (
    EntityShareData,
    EntityShareStatus,
)
from ai.backend.manager.models.clauses import QueryCondition, QueryOrder
from ai.backend.manager.models.entity_share.conditions import EntityShareConditions
from ai.backend.manager.models.entity_share.creators import EntityShareCreator
from ai.backend.manager.models.entity_share.orders import EntityShareOrders
from ai.backend.manager.models.entity_share.row import EntityShareRow
from ai.backend.manager.models.entity_share.searchers import EntityShareSearcher
from ai.backend.manager.services.entity_share.actions.answer import (
    AcceptEntityShareAction,
    CancelEntityShareAction,
    LeaveEntityShareAction,
    RejectEntityShareAction,
    RevokeEntityShareAction,
)
from ai.backend.manager.services.entity_share.actions.create import (
    CreateEntityShareAction,
)
from ai.backend.manager.services.entity_share.actions.get import GetEntityShareAction
from ai.backend.manager.services.entity_share.actions.search import (
    EntityShareRecipientProjectScopeItem,
    EntityShareRecipientScopeItem,
    EntityShareScopeItem,
    EntityShareSharerScopeItem,
    EntityShareTargetScopeItem,
    SearchEntitySharesAction,
)

__all__ = ("EntityShareAdapter",)


def _entity_share_pagination_spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=EntityShareOrders.created_at(ascending=True),
        backward_order=EntityShareOrders.created_at(ascending=False),
        forward_condition_factory=EntityShareConditions.by_cursor_forward,
        backward_condition_factory=EntityShareConditions.by_cursor_backward,
        tiebreaker_order=EntityShareRow.id.asc(),
    )


class EntityShareAdapter(BaseAdapter):
    """The REST v2 surface of the shares, one entity at a time.

    Creating takes one address rather than a list: an offer that clashes with an open
    one is that offer's answer, not the run's.
    """

    async def create(self, input: CreateEntityShareInput) -> EntitySharePayload:
        me = current_user()
        if me is None:
            raise UnreachableError("User context is not available")
        target = RuntimeEntityID(input.target_entity_type, input.target_entity_id)
        recipient: EntityIdentifier | None = None
        if input.recipient_project_id is not None:
            recipient = ProjectID(input.recipient_project_id)
        elif input.recipient_user_id is not None:
            recipient = UserID(input.recipient_user_id)
        result = await self._processors.entity_share.create.run(
            CreateEntityShareAction(
                creator=EntityShareCreator(
                    sharer_user_id=UserID(me.user_id),
                    target=target,
                    recipient=recipient,
                    recipient_email=input.recipient_email,
                    permission_cap=self._to_permission_cap(input.permissions),
                )
            )
        )
        return EntitySharePayload(share=self._to_node(result.data))

    async def get(self, share_id: EntityShareID) -> EntitySharePayload:
        result = await self._processors.entity_share.get.run(
            GetEntityShareAction(share_id=share_id)
        )
        return EntitySharePayload(share=self._to_node(result.data))

    async def accept(self, share_id: EntityShareID) -> EntitySharePayload:
        me = current_user()
        if me is None:
            raise UnreachableError("User context is not available")
        result = await self._processors.entity_share.accept.run(
            AcceptEntityShareAction(share_id=share_id, answering_scope=UserID(me.user_id))
        )
        return EntitySharePayload(share=self._to_node(result.data))

    async def reject(self, share_id: EntityShareID) -> EntitySharePayload:
        me = current_user()
        if me is None:
            raise UnreachableError("User context is not available")
        result = await self._processors.entity_share.reject.run(
            RejectEntityShareAction(share_id=share_id, answering_scope=UserID(me.user_id))
        )
        return EntitySharePayload(share=self._to_node(result.data))

    async def cancel(self, share_id: EntityShareID) -> EntitySharePayload:
        result = await self._processors.entity_share.cancel.run(
            CancelEntityShareAction(share_id=share_id)
        )
        return EntitySharePayload(share=self._to_node(result.data))

    async def revoke(self, share_id: EntityShareID) -> EntitySharePayload:
        result = await self._processors.entity_share.revoke.run(
            RevokeEntityShareAction(share_id=share_id)
        )
        return EntitySharePayload(share=self._to_node(result.data))

    async def leave(self, share_id: EntityShareID) -> EntitySharePayload:
        me = current_user()
        if me is None:
            raise UnreachableError("User context is not available")
        result = await self._processors.entity_share.leave.run(
            LeaveEntityShareAction(share_id=share_id, answering_scope=UserID(me.user_id))
        )
        return EntitySharePayload(share=self._to_node(result.data))

    async def my_search(self, input: MySearchEntitySharesInput) -> SearchEntitySharesPayload:
        """Page through the shares the caller stands on a side of.

        The same read the scoped query runs, with the caller filling the scope instead
        of naming it.
        """
        me = current_user()
        if me is None:
            raise UnreachableError("User context is not available")
        items: list[EntityShareScopeItem] = []
        for side in input.sides:
            match side:
                case EntityShareSideDTO.RECIPIENT:
                    items.append(EntityShareRecipientScopeItem(user_id=UserID(me.user_id)))
                case EntityShareSideDTO.SHARER:
                    items.append(EntityShareSharerScopeItem(user_id=UserID(me.user_id)))
        return await self._search(
            items,
            filter=input.filter,
            order=input.order,
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )

    async def scoped_search(
        self, input: ScopedSearchEntitySharesInput
    ) -> SearchEntitySharesPayload:
        """Page through the shares the named scopes reach, combined with OR.

        Every scope is authorized before the read runs, so naming another person's
        shares is refused unless the caller may reach that person's scope.
        """
        return await self._search(
            self._to_scope_items(input.scope),
            filter=input.filter,
            order=input.order,
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )

    async def _search(
        self,
        items: list[EntityShareScopeItem],
        *,
        filter: EntityShareFilter | None,
        order: list[EntityShareOrderBy] | None,
        first: int | None,
        after: str | None,
        last: int | None,
        before: str | None,
        limit: int | None,
        offset: int | None,
    ) -> SearchEntitySharesPayload:
        searcher = self._build_searcher(
            EntityShareSearcher,
            conditions=self._convert_filter(filter) if filter else [],
            orders=self._convert_orders(order) if order else [],
            pagination_spec=_entity_share_pagination_spec(),
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        )
        result = await self._processors.entity_share.search.run(
            SearchEntitySharesAction(items=items, searcher=searcher)
        )
        return SearchEntitySharesPayload(
            items=[self._to_node(d) for d in result.items],
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    def _to_scope_items(self, scope: EntityShareScope) -> list[EntityShareScopeItem]:
        items: list[EntityShareScopeItem] = []
        for recipient in scope.recipient or ():
            items.append(EntityShareRecipientScopeItem(user_id=UserID(recipient.value)))
        for project in scope.recipient_project or ():
            items.append(EntityShareRecipientProjectScopeItem(project_id=ProjectID(project.value)))
        for sharer in scope.sharer or ():
            items.append(EntityShareSharerScopeItem(user_id=UserID(sharer.value)))
        for target in scope.target or ():
            items.append(
                EntityShareTargetScopeItem(
                    target=RuntimeEntityID(target.entity_type, target.entity_id)
                )
            )
        return items

    def _to_permission_cap(self, permissions: Sequence[PermissionBitDTO]) -> Permission | None:
        """An empty list means no ceiling, which is what ``None`` says to the graph."""
        if not permissions:
            return None
        cap = Permission.NONE
        for permission in permissions:
            cap |= Permission[permission.name]
        return cap

    def _to_permission_dtos(self, cap: Permission | None) -> list[PermissionBitDTO]:
        if cap is None:
            return []
        return [dto for dto in PermissionBitDTO if cap & Permission[dto.name]]

    def _convert_filter(self, filter: EntityShareFilter) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []
        if filter.status is not None:
            if filter.status.equals is not None:
                conditions.append(
                    EntityShareConditions.by_status(EntityShareStatus(filter.status.equals))
                )
            if filter.status.in_ is not None:
                conditions.append(
                    EntityShareConditions.by_status_in([
                        EntityShareStatus(status) for status in filter.status.in_
                    ])
                )
        if filter.recipient_email is not None and filter.recipient_email.equals is not None:
            conditions.append(
                EntityShareConditions.by_recipient_email(filter.recipient_email.equals)
            )
        return conditions

    def _convert_orders(self, orders: Sequence[EntityShareOrderBy]) -> list[QueryOrder]:
        converted: list[QueryOrder] = []
        for order in orders:
            ascending = order.direction is OrderDirection.ASC
            match order.field:
                case EntityShareOrderField.CREATED_AT:
                    converted.append(EntityShareOrders.created_at(ascending))
                case EntityShareOrderField.UPDATED_AT:
                    converted.append(EntityShareOrders.updated_at(ascending))
                case EntityShareOrderField.STATUS:
                    converted.append(EntityShareOrders.status(ascending))
        return converted

    def _to_node(self, data: EntityShareData) -> EntityShareNode:
        return EntityShareNode(
            id=data.id,
            sharer_user_id=data.sharer_user_id,
            recipient_email=data.recipient_email,
            target_entity_type=data.target.entity_type(),
            target_entity_id=data.target,
            permissions=self._to_permission_dtos(data.permission_cap),
            status=EntityShareStatusDTO(data.status),
            created_at=data.created_at,
            updated_at=data.updated_at,
        )
