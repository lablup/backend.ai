from datetime import datetime
from typing import Optional
from uuid import UUID

import strawberry
from strawberry.relay import Connection, Node, NodeID, PageInfo
from strawberry.relay.types import NodeIterableType
from strawberry.types import Info

from ai.backend.manager.api.gql.base import JSONString


@strawberry.type
class RoutingNode(Node):
    id: NodeID
    routing_id: UUID
    endpoint: str
    session: UUID
    status: str
    traffic_ratio: float
    created_at: datetime
    live_stat: JSONString


@strawberry.type
class RoutingNodeConnection(Connection[RoutingNode]):
    @classmethod
    def resolve_connection(
        cls,
        nodes: NodeIterableType[RoutingNode],
        *,
        info: Info,
        before: Optional[str] = None,
        after: Optional[str] = None,
        first: Optional[int] = None,
        last: Optional[int] = None,
        max_results: Optional[int] = None,
        **kwargs,
    ) -> "RoutingNodeConnection":
        return cls(
            edges=[],
            page_info=PageInfo(
                has_next_page=False,
                has_previous_page=False,
                start_cursor=None,
                end_cursor=None,
            ),
        )
