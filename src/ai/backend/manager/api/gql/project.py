from __future__ import annotations

from collections.abc import Iterable
from typing import override

from strawberry import ID, Info, relay

from ai.backend.manager.api.gql.base import resolve_global_id
from ai.backend.manager.api.gql.decorators import BackendAIGQLMeta, gql_federation_type


@gql_federation_type(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Federation stub for legacy GroupNode.",
    ),
    name="GroupNode",
    keys=["id"],
    extend=True,
)
class Project(relay.Node):
    id: relay.NodeID[str]

    @classmethod
    @override
    def resolve_nodes(
        cls,
        *,
        info: Info,
        node_ids: Iterable[str],
        required: bool = False,
    ) -> list[Project]:
        return [cls(id=node_id) for node_id in node_ids]

    @classmethod
    def resolve_reference(cls, id: ID, info: Info) -> Project:
        return cls(id=resolve_global_id(str(id))[1])
