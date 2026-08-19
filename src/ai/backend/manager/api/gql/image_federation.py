"""
Federated Image (ImageNode) type with full field definitions for Strawberry GraphQL.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import override

from strawberry import ID, Info, relay

from ai.backend.manager.api.gql.base import resolve_global_id
from ai.backend.manager.api.gql.decorators import BackendAIGQLMeta, gql_federation_type


@gql_federation_type(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Federation stub for legacy ImageNode.",
    ),
    name="ImageNode",
    keys=["id"],
    extend=True,
)
class Image(relay.Node):
    """
    Federated type (ImageNode) bridging the legacy graphene subgraph into Relay node resolution.
    """

    id: relay.NodeID[str]

    @classmethod
    @override
    def resolve_nodes(
        cls,
        *,
        info: Info,
        node_ids: Iterable[str],
        required: bool = False,
    ) -> list[Image]:
        return [cls(id=node_id) for node_id in node_ids]

    @classmethod
    def resolve_reference(cls, id: ID, info: Info) -> Image:
        return cls(id=resolve_global_id(str(id))[1])
