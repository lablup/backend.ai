"""Relay ``node(id:)`` and ``nodes(ids:)`` root fields, owned by the Strawberry subgraph.

V2 Node types resolve in-process via ``resolve_nodes``; legacy graphene types resolve via their
federation stub (``_entities`` -> graphene ``__resolve_reference``).
"""

from __future__ import annotations

from typing import cast

from strawberry import Info, relay
from strawberry.federation.schema_directives import Override

from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
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


@gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Relay Global Object Identification: resolve Nodes by their global IDs, in the "
            "given order. An ID matching no node, or one the caller may not read, is null."
        ),
    ),
)  # type: ignore[misc]
def nodes(ids: list[relay.GlobalID], info: Info[StrawberryGQLContext]) -> list[relay.Node | None]:
    # One awaitable per id, so a failing id nulls only its own item; data loaders batch per type.
    return cast(list[relay.Node | None], [id.resolve_node(info, required=False) for id in ids])
