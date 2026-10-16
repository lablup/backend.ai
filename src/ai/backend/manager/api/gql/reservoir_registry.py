from collections.abc import Iterable, Sequence
from typing import Self, cast, override
from uuid import UUID

import strawberry
from strawberry import ID, UNSET, Info
from strawberry.relay import Connection, Edge, NodeID

from ai.backend.common.dto.manager.v2.common import PartialBulkPayload
from ai.backend.common.dto.manager.v2.reservoir_registry.request import (
    AdminSearchReservoirRegistriesInput,
)
from ai.backend.common.dto.manager.v2.reservoir_registry.request import (
    CreateReservoirRegistryInput as CreateReservoirRegistryInputDTO,
)
from ai.backend.common.dto.manager.v2.reservoir_registry.request import (
    DeleteReservoirRegistryInput as DeleteReservoirRegistryInputDTO,
)
from ai.backend.common.dto.manager.v2.reservoir_registry.request import (
    PartialBulkPurgeReservoirRegistriesInput as PartialBulkPurgeReservoirRegistriesInputDTO,
)
from ai.backend.common.dto.manager.v2.reservoir_registry.request import (
    PartialBulkUpdateReservoirRegistriesInput as PartialBulkUpdateReservoirRegistriesInputDTO,
)
from ai.backend.common.dto.manager.v2.reservoir_registry.request import (
    PartialBulkUpdateReservoirRegistryItemInput as PartialBulkUpdateReservoirRegistryItemInputDTO,
)
from ai.backend.common.dto.manager.v2.reservoir_registry.request import (
    UpdateReservoirRegistryBody as UpdateReservoirRegistryBodyDTO,
)
from ai.backend.common.dto.manager.v2.reservoir_registry.request import (
    UpdateReservoirRegistryInput as UpdateReservoirRegistryInputDTO,
)
from ai.backend.common.dto.manager.v2.reservoir_registry.response import (
    CreateReservoirRegistryPayload as CreateReservoirRegistryPayloadDTO,
)
from ai.backend.common.dto.manager.v2.reservoir_registry.response import (
    DeleteReservoirRegistryPayload as DeleteReservoirRegistryPayloadDTO,
)
from ai.backend.common.dto.manager.v2.reservoir_registry.response import (
    PurgeReservoirRegistryPayload as PurgeReservoirRegistryPayloadDTO,
)
from ai.backend.common.dto.manager.v2.reservoir_registry.response import ReservoirRegistryNode
from ai.backend.common.dto.manager.v2.reservoir_registry.response import (
    UpdateReservoirRegistryPayload as UpdateReservoirRegistryPayloadDTO,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.artifact_registry_meta import ArtifactRegistryMetaConnection
from ai.backend.manager.api.gql.base import encode_cursor, parse_uuid
from ai.backend.manager.api.gql.common_types import PartialBulkFailureGQL
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    PydanticInputMixin,
    gql_added_field,
    gql_connection_type,
    gql_field,
    gql_mutation,
    gql_node_type,
    gql_pydantic_input,
    gql_pydantic_type,
    gql_root_field,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticNodeMixin, PydanticOutputMixin
from ai.backend.manager.errors.api import NotImplementedAPI

from .types import StrawberryGQLContext


@gql_node_type(
    BackendAIGQLMeta(
        added_version="25.14.0",
        description="Reservoir registry node.",
    ),
)
class ReservoirRegistry(PydanticNodeMixin[ReservoirRegistryNode]):
    id: NodeID[str]
    entity_id: UUID = gql_added_field(
        BackendAIGQLMeta(
            added_version="26.9.0",
            description="UUID of the reservoir registry.",
        ),
    )
    name: str
    endpoint: str
    access_key: str
    secret_key: str
    api_version: str

    @classmethod
    @override
    async def resolve_nodes(  # type: ignore[override]  # Strawberry Node uses AwaitableOrValue overloads incompatible with async def
        cls,
        *,
        info: Info[StrawberryGQLContext],
        node_ids: Iterable[str],
        required: bool = False,
    ) -> Iterable[Self | None]:
        results = await info.context.data_loaders.reservoir_registry_loader.load_many([
            UUID(nid) for nid in node_ids
        ])
        return cast(list[Self | None], results)

    @classmethod
    async def load_by_id(
        cls, ctx: StrawberryGQLContext, reservoir_ids: Sequence[UUID]
    ) -> list["ReservoirRegistry"]:
        nodes = await ctx.adapters.reservoir_registry.get_many(list(reservoir_ids))
        return [ReservoirRegistry.from_pydantic(node) for node in nodes]

    @gql_field(description="The remote artifact registries of this entity.")  # type: ignore[misc]
    @classmethod
    async def remote_artifact_registries(
        cls, ctx: strawberry.Info[StrawberryGQLContext]
    ) -> ArtifactRegistryMetaConnection | None:
        raise NotImplementedAPI("This API is not implemented.")


ReservoirRegistryEdge = Edge[ReservoirRegistry]


@gql_connection_type(
    BackendAIGQLMeta(
        added_version="25.14.0",
        description="Relay-style connection for paginated reservoir registry queries.",
    ),
)
class ReservoirRegistryConnection(Connection[ReservoirRegistry]):
    @gql_field(description="The count of this entity.")  # type: ignore[misc]
    def count(self) -> int:
        return len(self.edges)


@gql_root_field(
    BackendAIGQLMeta(added_version="25.14.0", description="Get a reservoir registry by ID")
)  # type: ignore[misc]
async def reservoir_registry(id: ID, info: Info[StrawberryGQLContext]) -> ReservoirRegistry | None:
    node = await info.context.adapters.reservoir_registry.get(parse_uuid(id))
    return ReservoirRegistry.from_pydantic(node)


@gql_root_field(
    BackendAIGQLMeta(added_version="25.14.0", description="List all reservoir registries")
)  # type: ignore[misc]
async def reservoir_registries(
    info: Info[StrawberryGQLContext],
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    offset: int | None = None,
    limit: int | None = None,
) -> ReservoirRegistryConnection | None:
    payload = await info.context.adapters.reservoir_registry.search(
        AdminSearchReservoirRegistriesInput(
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        )
    )
    nodes = [ReservoirRegistry.from_pydantic(item) for item in payload.items]
    edges = [ReservoirRegistryEdge(node=node, cursor=encode_cursor(node.id)) for node in nodes]

    return ReservoirRegistryConnection(
        edges=edges,
        page_info=strawberry.relay.PageInfo(
            has_next_page=False,
            has_previous_page=False,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
    )


@gql_pydantic_input(
    BackendAIGQLMeta(description="", added_version="25.14.0"),
)
class CreateReservoirRegistryInput(PydanticInputMixin[CreateReservoirRegistryInputDTO]):
    name: str
    endpoint: str
    access_key: str
    secret_key: str
    api_version: str


@gql_pydantic_input(
    BackendAIGQLMeta(description="", added_version="25.14.0"),
)
class UpdateReservoirRegistryInput(PydanticInputMixin[UpdateReservoirRegistryInputDTO]):
    id: ID
    name: str | None = UNSET
    endpoint: str | None = UNSET
    access_key: str | None = UNSET
    secret_key: str | None = UNSET
    api_version: str | None = UNSET


@gql_pydantic_input(
    BackendAIGQLMeta(description="", added_version="25.14.0"),
)
class DeleteReservoirRegistryInput(PydanticInputMixin[DeleteReservoirRegistryInputDTO]):
    id: ID


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="25.14.0",
        description="Payload for creating a reservoir registry.",
    ),
    model=CreateReservoirRegistryPayloadDTO,
)
class CreateReservoirRegistryPayload(PydanticOutputMixin[CreateReservoirRegistryPayloadDTO]):
    reservoir: ReservoirRegistry


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="25.14.0",
        description="Payload for updating a reservoir registry.",
    ),
    model=UpdateReservoirRegistryPayloadDTO,
)
class UpdateReservoirRegistryPayload(PydanticOutputMixin[UpdateReservoirRegistryPayloadDTO]):
    reservoir: ReservoirRegistry


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="25.14.0",
        description="Payload for deleting a reservoir registry.",
    ),
    model=DeleteReservoirRegistryPayloadDTO,
)
class DeleteReservoirRegistryPayload(PydanticOutputMixin[DeleteReservoirRegistryPayloadDTO]):
    id: UUID = gql_field(description="ID of the deleted Reservoir registry")


@gql_mutation(BackendAIGQLMeta(added_version="25.14.0", description="Create reservoir registry."))
async def create_reservoir_registry(
    input: CreateReservoirRegistryInput, info: Info[StrawberryGQLContext]
) -> CreateReservoirRegistryPayload | None:
    result = await info.context.adapters.reservoir_registry.create(input.to_pydantic())
    return CreateReservoirRegistryPayload(
        reservoir=ReservoirRegistry.from_pydantic(result.reservoir)
    )


@gql_mutation(BackendAIGQLMeta(added_version="25.14.0", description="Update reservoir registry."))
async def update_reservoir_registry(
    input: UpdateReservoirRegistryInput, info: Info[StrawberryGQLContext]
) -> UpdateReservoirRegistryPayload | None:
    result = await info.context.adapters.reservoir_registry.update(input.to_pydantic())
    return UpdateReservoirRegistryPayload(
        reservoir=ReservoirRegistry.from_pydantic(result.reservoir)
    )


@gql_mutation(
    BackendAIGQLMeta(added_version="25.14.0", description="Delete reservoir registry."),
    deprecation_reason=f"Deprecated since {NEXT_RELEASE_VERSION}. Use `purgeReservoirRegistry`.",
)
async def delete_reservoir_registry(
    input: DeleteReservoirRegistryInput, info: Info[StrawberryGQLContext]
) -> DeleteReservoirRegistryPayload | None:
    result = await info.context.adapters.reservoir_registry.purge(input.to_pydantic().id)
    return DeleteReservoirRegistryPayload(id=result.id)


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Fields to update on a Reservoir registry.",
    ),
    name="UpdateReservoirRegistryBodyInput",
)
class UpdateReservoirRegistryBodyInputGQL(PydanticInputMixin[UpdateReservoirRegistryBodyDTO]):
    name: str | None = gql_field(default=UNSET, description="New registry name.")
    endpoint: str | None = gql_field(default=UNSET, description="New endpoint URL.")
    access_key: str | None = gql_field(default=UNSET, description="New access key.")
    secret_key: str | None = gql_field(default=UNSET, description="New secret key.")
    api_version: str | None = gql_field(default=UNSET, description="New API version.")


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="One Reservoir registry of a partial bulk update and the fields to update on it.",
    ),
    name="PartialBulkUpdateReservoirRegistryItemInput",
)
class PartialBulkUpdateReservoirRegistryItemInputGQL(
    PydanticInputMixin[PartialBulkUpdateReservoirRegistryItemInputDTO]
):
    id: UUID = gql_field(description="ID of the registry to update.")
    input: UpdateReservoirRegistryBodyInputGQL = gql_field(
        description="Fields to update on the registry."
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Input for updating several Reservoir registries, each answered for separately.",
    ),
    name="PartialBulkUpdateReservoirRegistriesInput",
)
class PartialBulkUpdateReservoirRegistriesInputGQL(
    PydanticInputMixin[PartialBulkUpdateReservoirRegistriesInputDTO]
):
    items: list[PartialBulkUpdateReservoirRegistryItemInputGQL] = gql_field(
        description="The registries to update, each with its fields."
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Input for purging several Reservoir registries, each answered for separately.",
    ),
    name="PartialBulkPurgeReservoirRegistriesInput",
)
class PartialBulkPurgeReservoirRegistriesInputGQL(
    PydanticInputMixin[PartialBulkPurgeReservoirRegistriesInputDTO]
):
    ids: list[UUID] = gql_field(description="IDs of the registries to purge.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Payload for purging a Reservoir registry.",
    ),
    model=PurgeReservoirRegistryPayloadDTO,
    name="PurgeReservoirRegistryPayload",
)
class PurgeReservoirRegistryPayloadGQL(PydanticOutputMixin[PurgeReservoirRegistryPayloadDTO]):
    id: UUID = gql_field(description="ID of the purged Reservoir registry.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Result of a partial bulk Reservoir registry update: the registries updated and "
            "the ones that failed."
        ),
    ),
    model=PartialBulkPayload[ReservoirRegistryNode],
    name="PartialBulkUpdateReservoirRegistriesPayload",
)
class PartialBulkUpdateReservoirRegistriesPayloadGQL(
    PydanticOutputMixin[PartialBulkPayload[ReservoirRegistryNode]]
):
    successes: list[ReservoirRegistry] = gql_field(
        description="The registries updated, as they now stand."
    )
    failed: list[PartialBulkFailureGQL] = gql_field(
        description="The registries not updated, each with the reason."
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Result of a partial bulk Reservoir registry purge: the registries purged and "
            "the ones that failed."
        ),
    ),
    model=PartialBulkPayload[PurgeReservoirRegistryPayloadDTO],
    name="PartialBulkPurgeReservoirRegistriesPayload",
)
class PartialBulkPurgeReservoirRegistriesPayloadGQL(
    PydanticOutputMixin[PartialBulkPayload[PurgeReservoirRegistryPayloadDTO]]
):
    successes: list[PurgeReservoirRegistryPayloadGQL] = gql_field(
        description="The registries purged."
    )
    failed: list[PartialBulkFailureGQL] = gql_field(
        description="The registries not purged, each with the reason."
    )


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Permanently delete a Reservoir registry.",
    )
)
async def purge_reservoir_registry(
    info: Info[StrawberryGQLContext],
    id: UUID,
) -> PurgeReservoirRegistryPayloadGQL:
    payload = await info.context.adapters.reservoir_registry.purge(id)
    return PurgeReservoirRegistryPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Update several Reservoir registries, answering for each one.",
    )
)
async def partial_bulk_update_reservoir_registries(
    info: Info[StrawberryGQLContext],
    input: PartialBulkUpdateReservoirRegistriesInputGQL,
) -> PartialBulkUpdateReservoirRegistriesPayloadGQL:
    payload = await info.context.adapters.reservoir_registry.partial_bulk_update(
        input.to_pydantic()
    )
    return PartialBulkUpdateReservoirRegistriesPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Permanently delete several Reservoir registries, answering for each one.",
    )
)
async def partial_bulk_purge_reservoir_registries(
    info: Info[StrawberryGQLContext],
    input: PartialBulkPurgeReservoirRegistriesInputGQL,
) -> PartialBulkPurgeReservoirRegistriesPayloadGQL:
    payload = await info.context.adapters.reservoir_registry.partial_bulk_purge(input.to_pydantic())
    return PartialBulkPurgeReservoirRegistriesPayloadGQL.from_pydantic(payload)
