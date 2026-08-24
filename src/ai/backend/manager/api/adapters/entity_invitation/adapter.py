from __future__ import annotations

from collections.abc import Sequence

from ai.backend.common.contexts.user import current_user
from ai.backend.common.data.entity.entity_invitation import EntityInvitationID
from ai.backend.common.data.entity.types import RuntimeEntityID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.dto.manager.v2.common import OrderDirection
from ai.backend.common.dto.manager.v2.entity_invitation.request import (
    CreateEntityInvitationInput,
    EntityInvitationFilter,
    EntityInvitationOrderBy,
    EntityInvitationScopeItemDTO,
    ScopedSearchEntityInvitationsInput,
)
from ai.backend.common.dto.manager.v2.entity_invitation.response import (
    EntityInvitationNode,
    EntityInvitationPayload,
    SearchEntityInvitationsPayload,
)
from ai.backend.common.dto.manager.v2.entity_invitation.types import (
    EntityInvitationOrderField,
    EntityInvitationSideDTO,
    EntityInvitationStatusDTO,
)
from ai.backend.common.dto.manager.v2.rbac.types import PermissionBitDTO
from ai.backend.common.exception import UnreachableError
from ai.backend.manager.api.adapter_options.pagination.pagination import PaginationSpec
from ai.backend.manager.api.adapters.base import BaseAdapter
from ai.backend.manager.data.entity_invitation.types import (
    EntityInvitationData,
    EntityInvitationStatus,
)
from ai.backend.manager.models.clauses import QueryCondition, QueryOrder
from ai.backend.manager.models.entity_invitation.conditions import EntityInvitationConditions
from ai.backend.manager.models.entity_invitation.creators import EntityInvitationCreator
from ai.backend.manager.models.entity_invitation.orders import EntityInvitationOrders
from ai.backend.manager.models.entity_invitation.row import EntityInvitationRow
from ai.backend.manager.models.entity_invitation.searchers import EntityInvitationSearcher
from ai.backend.manager.services.entity_invitation.actions.answer import (
    AcceptEntityInvitationAction,
    CancelEntityInvitationAction,
    RejectEntityInvitationAction,
)
from ai.backend.manager.services.entity_invitation.actions.create import (
    CreateEntityInvitationAction,
)
from ai.backend.manager.services.entity_invitation.actions.get import GetEntityInvitationAction
from ai.backend.manager.services.entity_invitation.actions.search import (
    EntityInvitationScopeItem,
    ReceivedEntityInvitationScopeItem,
    SearchEntityInvitationsAction,
    SentEntityInvitationScopeItem,
    TargetEntityInvitationScopeItem,
)

__all__ = ("EntityInvitationAdapter",)


def _entity_invitation_pagination_spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=EntityInvitationOrders.created_at(ascending=True),
        backward_order=EntityInvitationOrders.created_at(ascending=False),
        forward_condition_factory=EntityInvitationConditions.by_cursor_forward,
        backward_condition_factory=EntityInvitationConditions.by_cursor_backward,
        tiebreaker_order=EntityInvitationRow.id.asc(),
    )


class EntityInvitationAdapter(BaseAdapter):
    """The REST v2 surface of the invitations, one entity at a time.

    Creating takes one address rather than a list: an offer that clashes with an open
    one is that offer's answer, not the run's.
    """

    async def create(self, input: CreateEntityInvitationInput) -> EntityInvitationPayload:
        me = current_user()
        if me is None:
            raise UnreachableError("User context is not available")
        target = RuntimeEntityID(input.target_entity_type, input.target_entity_id)
        result = await self._processors.entity_invitation.create.run(
            CreateEntityInvitationAction(
                creator=EntityInvitationCreator(
                    inviter_user_id=UserID(me.user_id),
                    invitee_email=input.invitee_email,
                    target=target,
                    permission_cap=self._to_permission_cap(input.permissions),
                )
            )
        )
        return EntityInvitationPayload(invitation=self._to_node(result.data))

    async def get(self, invitation_id: EntityInvitationID) -> EntityInvitationPayload:
        result = await self._processors.entity_invitation.get.run(
            GetEntityInvitationAction(invitation_id=invitation_id)
        )
        return EntityInvitationPayload(invitation=self._to_node(result.data))

    async def accept(self, invitation_id: EntityInvitationID) -> EntityInvitationPayload:
        me = current_user()
        if me is None:
            raise UnreachableError("User context is not available")
        result = await self._processors.entity_invitation.accept.run(
            AcceptEntityInvitationAction(
                invitation_id=invitation_id, invitee_user_id=UserID(me.user_id)
            )
        )
        return EntityInvitationPayload(invitation=self._to_node(result.data))

    async def reject(self, invitation_id: EntityInvitationID) -> EntityInvitationPayload:
        me = current_user()
        if me is None:
            raise UnreachableError("User context is not available")
        result = await self._processors.entity_invitation.reject.run(
            RejectEntityInvitationAction(
                invitation_id=invitation_id, invitee_user_id=UserID(me.user_id)
            )
        )
        return EntityInvitationPayload(invitation=self._to_node(result.data))

    async def cancel(self, invitation_id: EntityInvitationID) -> EntityInvitationPayload:
        result = await self._processors.entity_invitation.cancel.run(
            CancelEntityInvitationAction(invitation_id=invitation_id)
        )
        return EntityInvitationPayload(invitation=self._to_node(result.data))

    async def scoped_search(
        self, input: ScopedSearchEntityInvitationsInput
    ) -> SearchEntityInvitationsPayload:
        """Page through the invitations the named sides reach, combined with OR.

        The two sides answered for by the requester name nobody: whose invitations they
        are comes from the caller's identity, not from what they sent.
        """
        items = [self._to_scope_item(item) for item in input.scope.items]
        searcher = self._build_searcher(
            EntityInvitationSearcher,
            conditions=self._convert_filter(input.filter) if input.filter else [],
            orders=self._convert_orders(input.order) if input.order else [],
            pagination_spec=_entity_invitation_pagination_spec(),
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )
        result = await self._processors.entity_invitation.search.run(
            SearchEntityInvitationsAction(items=items, searcher=searcher)
        )
        return SearchEntityInvitationsPayload(
            items=[self._to_node(d) for d in result.items],
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    def _to_scope_item(self, item: EntityInvitationScopeItemDTO) -> EntityInvitationScopeItem:
        match item.side:
            case EntityInvitationSideDTO.RECEIVED:
                return ReceivedEntityInvitationScopeItem(user_id=self._me())
            case EntityInvitationSideDTO.SENT:
                return SentEntityInvitationScopeItem(user_id=self._me())
            case EntityInvitationSideDTO.TARGET:
                entity_type = item.target_entity_type
                entity_id = item.target_entity_id
                if entity_type is None or entity_id is None:
                    raise UnreachableError("A TARGET item naming nothing is refused when parsed")
                return TargetEntityInvitationScopeItem(
                    target=RuntimeEntityID(entity_type, entity_id)
                )

    def _me(self) -> UserID:
        me = current_user()
        if me is None:
            raise UnreachableError("User context is not available")
        return UserID(me.user_id)

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

    def _convert_filter(self, filter: EntityInvitationFilter) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []
        if filter.status is not None:
            if filter.status.equals is not None:
                conditions.append(
                    EntityInvitationConditions.by_status(
                        EntityInvitationStatus(filter.status.equals)
                    )
                )
            if filter.status.in_ is not None:
                conditions.append(
                    EntityInvitationConditions.by_status_in([
                        EntityInvitationStatus(status) for status in filter.status.in_
                    ])
                )
        if filter.invitee_email is not None and filter.invitee_email.equals is not None:
            conditions.append(
                EntityInvitationConditions.by_invitee_email(filter.invitee_email.equals)
            )
        return conditions

    def _convert_orders(self, orders: Sequence[EntityInvitationOrderBy]) -> list[QueryOrder]:
        converted: list[QueryOrder] = []
        for order in orders:
            ascending = order.direction is OrderDirection.ASC
            match order.field:
                case EntityInvitationOrderField.CREATED_AT:
                    converted.append(EntityInvitationOrders.created_at(ascending))
                case EntityInvitationOrderField.UPDATED_AT:
                    converted.append(EntityInvitationOrders.updated_at(ascending))
                case EntityInvitationOrderField.STATUS:
                    converted.append(EntityInvitationOrders.status(ascending))
        return converted

    def _to_node(self, data: EntityInvitationData) -> EntityInvitationNode:
        return EntityInvitationNode(
            id=data.id,
            inviter_user_id=data.inviter_user_id,
            invitee_email=data.invitee_email,
            target_entity_type=data.target_entity_type,
            target_entity_id=data.target_entity_id,
            permissions=self._to_permission_dtos(data.permission_cap),
            status=EntityInvitationStatusDTO(data.status),
            created_at=data.created_at,
            updated_at=data.updated_at,
        )
