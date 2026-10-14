from __future__ import annotations

from collections.abc import Iterable

from strawberry import ID, Info, relay

from ai.backend.manager.api.gql.base import resolve_global_id
from ai.backend.manager.api.gql.decorators import BackendAIGQLMeta, gql_federation_type


@gql_federation_type(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Federation stub for legacy DomainNode.",
    ),
    name="DomainNode",
    keys=["id"],
    extend=True,
)
class Domain(relay.Node):
    id: relay.NodeID[str]

    @classmethod
    def resolve_nodes(
        cls,
        *,
        info: Info,
        node_ids: Iterable[str],
        required: bool = False,
    ) -> list[Domain]:
        return [cls(id=node_id) for node_id in node_ids]

    @classmethod
    def resolve_reference(cls, id: ID, info: Info) -> Domain:
        return cls(id=resolve_global_id(str(id))[1])
