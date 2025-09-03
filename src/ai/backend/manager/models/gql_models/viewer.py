from __future__ import annotations

from base64 import b64encode
from typing import (
    TYPE_CHECKING,
    Optional,
    Self,
)

import graphene
import graphene_federation

from ai.backend.common.contexts.user import current_user

from ..gql_relay import AsyncNode
from .user import UserNode

if TYPE_CHECKING:
    from ..gql import GraphQueryContext


__all__ = ("Viewer",)


@graphene_federation.key("id")
class Viewer(graphene.ObjectType):
    class Meta:
        interfaces = (AsyncNode,)

    user = graphene.Field(UserNode)
    encoded_user_role = graphene.String()

    async def resolve_encoded_user_role(self, info: graphene.ResolveInfo) -> str:
        role: str = self.user.role
        return b64encode(role.encode()).decode()

    @classmethod
    async def get_viewer(cls, info: graphene.ResolveInfo) -> Optional[Self]:
        user = current_user()
        if user is None:
            return None

        graph_ctx: GraphQueryContext = info.context
        full_user_data = await graph_ctx.user_repository.get_user_by_uuid(user.user_id)
        user_node = UserNode.from_dataclass(graph_ctx, full_user_data)
        return cls(
            id=full_user_data.id,
            user=user_node,
        )
