"""Relay ``node(id:)`` root field, owned by the Strawberry subgraph via federation ``@override``.

V2 Node types resolve in-process via ``resolve_nodes``; legacy graphene types resolve via their
federation stub (``_entities`` -> graphene ``__resolve_reference``).
"""

from __future__ import annotations

from strawberry import Info, relay
from strawberry.federation.schema_directives import Override

from ai.backend.manager.api.gql.decorators import BackendAIGQLMeta, gql_root_field
from ai.backend.manager.api.gql.types import StrawberryGQLContext


@gql_root_field(
    BackendAIGQLMeta(
        added_version="26.7.0",
        description="Relay Global Object Identification: resolve any Node by its global ID.",
    ),
    directives=[Override(override_from="graphene")],
)  # type: ignore[misc]
async def node(id: relay.GlobalID, info: Info[StrawberryGQLContext]) -> relay.Node | None:
    return await id.resolve_node(info, required=False)
