"""Federation stubs that bridge legacy graphene Node types into the Strawberry-owned Relay
``node(id:)`` resolver.

Each stub implements ``relay.Node`` (so the Strawberry ``node`` field can return it) and is a
federation ``@key`` entity (so the Apollo Router resolves its real fields from the graphene
subgraph via ``_entities``). The matching graphene type must expose ``@graphene_federation.key``
+ ``__resolve_reference``.

Stubs whose corresponding graphene type is *already* referenced by a V2 field live next to that
field (``session_federation.py``, ``image_federation.py``, ``domain.py``, ``project.py``,
``vfolder.py``, ``user_federation.py``, ``resource_group/federation.py``). The stubs here cover
legacy Node types that have no V2 cross-reference but are still reachable via ``node(id:)`` today.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import override

from strawberry import ID, Info, relay

from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.base import resolve_global_id
from ai.backend.manager.api.gql.decorators import BackendAIGQLMeta, gql_federation_type


@gql_federation_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Federation stub for legacy AgentNode.",
    ),
    name="AgentNode",
    keys=["id"],
    extend=True,
)
class AgentNodeStub(relay.Node):
    id: relay.NodeID[str]

    @classmethod
    @override
    def resolve_nodes(
        cls, *, info: Info, node_ids: Iterable[str], required: bool = False
    ) -> list[AgentNodeStub]:
        return [cls(id=node_id) for node_id in node_ids]

    @classmethod
    def resolve_reference(cls, id: ID, info: Info) -> AgentNodeStub:
        return cls(id=resolve_global_id(str(id))[1])


@gql_federation_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Federation stub for legacy NetworkNode.",
    ),
    name="NetworkNode",
    keys=["id"],
    extend=True,
)
class NetworkNodeStub(relay.Node):
    id: relay.NodeID[str]

    @classmethod
    @override
    def resolve_nodes(
        cls, *, info: Info, node_ids: Iterable[str], required: bool = False
    ) -> list[NetworkNodeStub]:
        return [cls(id=node_id) for node_id in node_ids]

    @classmethod
    def resolve_reference(cls, id: ID, info: Info) -> NetworkNodeStub:
        return cls(id=resolve_global_id(str(id))[1])


@gql_federation_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Federation stub for legacy ModelCard.",
    ),
    name="ModelCard",
    keys=["id"],
    extend=True,
)
class ModelCardStub(relay.Node):
    id: relay.NodeID[str]

    @classmethod
    @override
    def resolve_nodes(
        cls, *, info: Info, node_ids: Iterable[str], required: bool = False
    ) -> list[ModelCardStub]:
        return [cls(id=node_id) for node_id in node_ids]

    @classmethod
    def resolve_reference(cls, id: ID, info: Info) -> ModelCardStub:
        return cls(id=resolve_global_id(str(id))[1])


@gql_federation_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Federation stub for legacy ContainerRegistryNode.",
    ),
    name="ContainerRegistryNode",
    keys=["id"],
    extend=True,
)
class ContainerRegistryNodeStub(relay.Node):
    id: relay.NodeID[str]

    @classmethod
    @override
    def resolve_nodes(
        cls, *, info: Info, node_ids: Iterable[str], required: bool = False
    ) -> list[ContainerRegistryNodeStub]:
        return [cls(id=node_id) for node_id in node_ids]

    @classmethod
    def resolve_reference(cls, id: ID, info: Info) -> ContainerRegistryNodeStub:
        return cls(id=resolve_global_id(str(id))[1])
