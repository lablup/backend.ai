from __future__ import annotations

from collections.abc import Iterable

from strawberry import ID, Info, relay

from ai.backend.manager.api.gql.base import resolve_global_id
from ai.backend.manager.api.gql.decorators import BackendAIGQLMeta, gql_federation_type


@gql_federation_type(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Federation stub for legacy ComputeSessionNode.",
    ),
    name="ComputeSessionNode",
    keys=["id"],
    extend=True,
)
class Session(relay.Node):
    id: relay.NodeID[str]

    @classmethod
    def resolve_nodes(
        cls,
        *,
        info: Info,
        node_ids: Iterable[str],
        required: bool = False,
    ) -> list[Session]:
        # Legacy node owned by the graphene subgraph: return id-only stubs;
        # the router resolves the remaining fields from graphene via _entities.
        return [cls(id=node_id) for node_id in node_ids]

    @classmethod
    def resolve_reference(cls, id: ID, info: Info) -> Session:
        return cls(id=resolve_global_id(str(id))[1])
