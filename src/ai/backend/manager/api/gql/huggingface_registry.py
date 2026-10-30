from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Self, cast, override
from uuid import UUID

import strawberry
from strawberry import ID, UNSET, Info
from strawberry.relay import Connection, Edge, NodeID

from ai.backend.common.dto.manager.v2.common import PartialBulkPayload
from ai.backend.common.dto.manager.v2.huggingface_registry.request import (
    AdminSearchHuggingFaceRegistriesInput,
)
from ai.backend.common.dto.manager.v2.huggingface_registry.request import (
    CreateHuggingFaceRegistryInput as CreateHuggingFaceRegistryInputDTO,
)
from ai.backend.common.dto.manager.v2.huggingface_registry.request import (
    DeleteHuggingFaceRegistryInput as DeleteHuggingFaceRegistryInputDTO,
)
from ai.backend.common.dto.manager.v2.huggingface_registry.request import (
    PartialBulkPurgeHuggingFaceRegistriesInput as PartialBulkPurgeHuggingFaceRegistriesInputDTO,
)
from ai.backend.common.dto.manager.v2.huggingface_registry.request import (
    PartialBulkUpdateHuggingFaceRegistriesInput as PartialBulkUpdateHuggingFaceRegistriesInputDTO,
)
from ai.backend.common.dto.manager.v2.huggingface_registry.request import (
    PartialBulkUpdateHuggingFaceRegistryItemInput as PartialBulkUpdateHuggingFaceRegistryItemInputDTO,
)
from ai.backend.common.dto.manager.v2.huggingface_registry.request import (
    UpdateHuggingFaceRegistryBody as UpdateHuggingFaceRegistryBodyDTO,
)
from ai.backend.common.dto.manager.v2.huggingface_registry.request import (
    UpdateHuggingFaceRegistryInput as UpdateHuggingFaceRegistryInputDTO,
)
from ai.backend.common.dto.manager.v2.huggingface_registry.response import (
    CreateHuggingFaceRegistryPayload as CreateHuggingFaceRegistryPayloadDTO,
)
from ai.backend.common.dto.manager.v2.huggingface_registry.response import (
    DeleteHuggingFaceRegistryPayload as DeleteHuggingFaceRegistryPayloadDTO,
)
from ai.backend.common.dto.manager.v2.huggingface_registry.response import (
    HuggingFaceRegistryNode,
)
from ai.backend.common.dto.manager.v2.huggingface_registry.response import (
    PurgeHuggingFaceRegistryPayload as PurgeHuggingFaceRegistryPayloadDTO,
)
from ai.backend.common.dto.manager.v2.huggingface_registry.response import (
    UpdateHuggingFaceRegistryPayload as UpdateHuggingFaceRegistryPayloadDTO,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.base import encode_cursor, parse_uuid, to_global_id
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

from .types import StrawberryGQLContext


@gql_node_type(
    BackendAIGQLMeta(
        added_version="25.14.0",
        description="HuggingFace registry node.",
    ),
)
class HuggingFaceRegistry(PydanticNodeMixin[HuggingFaceRegistryNode]):
    id: NodeID[str]
    entity_id: UUID = gql_added_field(
        BackendAIGQLMeta(
            added_version="26.9.0",
            description="UUID of the HuggingFace registry.",
        ),
    )
    url: str
    name: str
    token: str | None

    @classmethod
    @override
    async def resolve_nodes(  # type: ignore[override]  # Strawberry Node uses AwaitableOrValue overloads incompatible with async def
        cls,
        *,
        info: Info[StrawberryGQLContext],
        node_ids: Iterable[str],
        required: bool = False,
    ) -> Iterable[Self | None]:
        results = await info.context.data_loaders.huggingface_registry_loader.load_many([
            UUID(nid) for nid in node_ids
        ])
        return cast(list[Self | None], results)

    @classmethod
    async def load_by_id(
        cls, ctx: StrawberryGQLContext, registry_ids: Sequence[UUID]
    ) -> list[HuggingFaceRegistry]:
        nodes = await ctx.adapters.huggingface_registry.get_many(list(registry_ids))
        return [HuggingFaceRegistry.from_pydantic(node) for node in nodes]


HuggingFaceRegistryEdge = Edge[HuggingFaceRegistry]


@gql_connection_type(
    BackendAIGQLMeta(
        added_version="25.14.0",
        description="Relay-style connection for paginated HuggingFace registry queries.",
    ),
)
class HuggingFaceRegistryConnection(Connection[HuggingFaceRegistry]):
    @gql_field(description="The count of this entity.")  # type: ignore[misc]
    def count(self) -> int:
        return len(self.edges)


@gql_root_field(
    BackendAIGQLMeta(added_version="25.14.0", description="Get a HuggingFace registry by ID")
)  # type: ignore[misc]
async def huggingface_registry(
    id: ID, info: Info[StrawberryGQLContext]
) -> HuggingFaceRegistry | None:
    node = await info.context.adapters.huggingface_registry.get(parse_uuid(id))
    return HuggingFaceRegistry.from_pydantic(node)


@gql_root_field(
    BackendAIGQLMeta(added_version="25.14.0", description="List all HuggingFace registries")
)  # type: ignore[misc]
async def huggingface_registries(
    info: Info[StrawberryGQLContext],
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    offset: int | None = None,
    limit: int | None = None,
) -> HuggingFaceRegistryConnection | None:
    payload = await info.context.adapters.huggingface_registry.search(
        AdminSearchHuggingFaceRegistriesInput(
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        )
    )
    nodes = [HuggingFaceRegistry.from_pydantic(item) for item in payload.items]
    edges = [HuggingFaceRegistryEdge(node=node, cursor=encode_cursor(node.id)) for node in nodes]

    return HuggingFaceRegistryConnection(
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
class CreateHuggingFaceRegistryInput(PydanticInputMixin[CreateHuggingFaceRegistryInputDTO]):
    name: str
    url: str
    token: str | None = None


@gql_pydantic_input(
    BackendAIGQLMeta(description="", added_version="25.14.0"),
)
class UpdateHuggingFaceRegistryInput(PydanticInputMixin[UpdateHuggingFaceRegistryInputDTO]):
    id: ID
    url: str | None = UNSET
    name: str | None = UNSET
    token: str | None = UNSET


@gql_pydantic_input(
    BackendAIGQLMeta(description="", added_version="25.14.0"),
)
class DeleteHuggingFaceRegistryInput(PydanticInputMixin[DeleteHuggingFaceRegistryInputDTO]):
    id: ID


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="25.14.0",
        description="Payload for creating a HuggingFace registry.",
    ),
    model=CreateHuggingFaceRegistryPayloadDTO,
)
class CreateHuggingFaceRegistryPayload(PydanticOutputMixin[CreateHuggingFaceRegistryPayloadDTO]):
    huggingface_registry: HuggingFaceRegistry


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="25.14.0",
        description="Payload for updating a HuggingFace registry.",
    ),
    model=UpdateHuggingFaceRegistryPayloadDTO,
)
class UpdateHuggingFaceRegistryPayload(PydanticOutputMixin[UpdateHuggingFaceRegistryPayloadDTO]):
    huggingface_registry: HuggingFaceRegistry


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="25.14.0",
        description="Payload for deleting a HuggingFace registry.",
    ),
    model=DeleteHuggingFaceRegistryPayloadDTO,
)
class DeleteHuggingFaceRegistryPayload(PydanticOutputMixin[DeleteHuggingFaceRegistryPayloadDTO]):
    id: UUID = gql_field(description="ID of the deleted HuggingFace registry")


@gql_mutation(BackendAIGQLMeta(added_version="25.14.0", description="Create huggingface registry."))
async def create_huggingface_registry(
    input: CreateHuggingFaceRegistryInput, info: Info[StrawberryGQLContext]
) -> CreateHuggingFaceRegistryPayload | None:
    result = await info.context.adapters.huggingface_registry.create(input.to_pydantic())
    return CreateHuggingFaceRegistryPayload(
        huggingface_registry=HuggingFaceRegistry.from_pydantic(result.huggingface_registry)
    )


@gql_mutation(BackendAIGQLMeta(added_version="25.14.0", description="Update huggingface registry."))
async def update_huggingface_registry(
    input: UpdateHuggingFaceRegistryInput, info: Info[StrawberryGQLContext]
) -> UpdateHuggingFaceRegistryPayload | None:
    result = await info.context.adapters.huggingface_registry.update(input.to_pydantic())
    return UpdateHuggingFaceRegistryPayload(
        huggingface_registry=HuggingFaceRegistry.from_pydantic(result.huggingface_registry)
    )


@gql_mutation(
    BackendAIGQLMeta(added_version="25.14.0", description="Delete huggingface registry."),
    deprecation_reason=f"Deprecated since {NEXT_RELEASE_VERSION}. Use `purgeHuggingfaceRegistry`.",
)
async def delete_huggingface_registry(
    input: DeleteHuggingFaceRegistryInput, info: Info[StrawberryGQLContext]
) -> DeleteHuggingFaceRegistryPayload | None:
    result = await info.context.adapters.huggingface_registry.purge(input.to_pydantic().id)
    return DeleteHuggingFaceRegistryPayload(id=result.id)


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Fields to update on a HuggingFace registry.",
    ),
    name="UpdateHuggingFaceRegistryBodyInput",
)
class UpdateHuggingFaceRegistryBodyInputGQL(PydanticInputMixin[UpdateHuggingFaceRegistryBodyDTO]):
    name: str | None = gql_field(default=UNSET, description="New registry name.")
    url: str | None = gql_field(default=UNSET, description="New HuggingFace Hub URL.")
    token: str | None = gql_field(default=UNSET, description="New access token.")


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="One HuggingFace registry of a partial bulk update and the fields to update on it.",
    ),
    name="PartialBulkUpdateHuggingFaceRegistryItemInput",
)
class PartialBulkUpdateHuggingFaceRegistryItemInputGQL(
    PydanticInputMixin[PartialBulkUpdateHuggingFaceRegistryItemInputDTO]
):
    id: UUID = gql_field(description="ID of the registry to update.")
    input: UpdateHuggingFaceRegistryBodyInputGQL = gql_field(
        description="Fields to update on the registry."
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Input for updating several HuggingFace registries, each answered for separately.",
    ),
    name="PartialBulkUpdateHuggingFaceRegistriesInput",
)
class PartialBulkUpdateHuggingFaceRegistriesInputGQL(
    PydanticInputMixin[PartialBulkUpdateHuggingFaceRegistriesInputDTO]
):
    items: list[PartialBulkUpdateHuggingFaceRegistryItemInputGQL] = gql_field(
        description="The registries to update, each with its fields."
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Input for purging several HuggingFace registries, each answered for separately.",
    ),
    name="PartialBulkPurgeHuggingFaceRegistriesInput",
)
class PartialBulkPurgeHuggingFaceRegistriesInputGQL(
    PydanticInputMixin[PartialBulkPurgeHuggingFaceRegistriesInputDTO]
):
    ids: list[UUID] = gql_field(description="IDs of the registries to purge.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Payload for purging a HuggingFace registry.",
    ),
    model=PurgeHuggingFaceRegistryPayloadDTO,
    name="PurgeHuggingFaceRegistryPayload",
)
class PurgeHuggingFaceRegistryPayloadGQL(PydanticOutputMixin[PurgeHuggingFaceRegistryPayloadDTO]):
    id: UUID = gql_field(
        description="ID of the purged HuggingFace registry.",
        deprecation_reason=f"Deprecated since {NEXT_RELEASE_VERSION}. Use `purgedId` or `entityId`.",
    )
    purged_id: strawberry.ID = gql_added_field(
        BackendAIGQLMeta(
            added_version=NEXT_RELEASE_VERSION,
            description="Global ID of the purged HuggingFace registry.",
        ),
    )
    entity_id: UUID = gql_added_field(
        BackendAIGQLMeta(
            added_version=NEXT_RELEASE_VERSION,
            description="UUID of the purged HuggingFace registry.",
        ),
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Result of a partial bulk HuggingFace registry update: the registries updated and "
            "the ones that failed."
        ),
    ),
    model=PartialBulkPayload[HuggingFaceRegistryNode],
    name="PartialBulkUpdateHuggingFaceRegistriesPayload",
)
class PartialBulkUpdateHuggingFaceRegistriesPayloadGQL(
    PydanticOutputMixin[PartialBulkPayload[HuggingFaceRegistryNode]]
):
    successes: list[HuggingFaceRegistry] = gql_field(
        description="The registries updated, as they now stand."
    )
    failed: list[PartialBulkFailureGQL] = gql_field(
        description="The registries not updated, each with the reason."
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Result of a partial bulk HuggingFace registry purge: the registries purged and "
            "the ones that failed."
        ),
    ),
    model=PartialBulkPayload[PurgeHuggingFaceRegistryPayloadDTO],
    name="PartialBulkPurgeHuggingFaceRegistriesPayload",
)
class PartialBulkPurgeHuggingFaceRegistriesPayloadGQL(
    PydanticOutputMixin[PartialBulkPayload[PurgeHuggingFaceRegistryPayloadDTO]]
):
    successes: list[PurgeHuggingFaceRegistryPayloadGQL] = gql_field(
        description="The registries purged."
    )
    failed: list[PartialBulkFailureGQL] = gql_field(
        description="The registries not purged, each with the reason."
    )


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Permanently delete a HuggingFace registry.",
    )
)
async def purge_huggingface_registry(
    info: Info[StrawberryGQLContext],
    id: UUID,
) -> PurgeHuggingFaceRegistryPayloadGQL:
    payload = await info.context.adapters.huggingface_registry.purge(id)
    return PurgeHuggingFaceRegistryPayloadGQL.from_pydantic(
        payload, extra={"purged_id": to_global_id(HuggingFaceRegistry, payload.entity_id)}
    )


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Update several HuggingFace registries, answering for each one.",
    )
)
async def partial_bulk_update_huggingface_registries(
    info: Info[StrawberryGQLContext],
    input: PartialBulkUpdateHuggingFaceRegistriesInputGQL,
) -> PartialBulkUpdateHuggingFaceRegistriesPayloadGQL:
    payload = await info.context.adapters.huggingface_registry.partial_bulk_update(
        input.to_pydantic()
    )
    return PartialBulkUpdateHuggingFaceRegistriesPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Permanently delete several HuggingFace registries, answering for each one.",
    )
)
async def partial_bulk_purge_huggingface_registries(
    info: Info[StrawberryGQLContext],
    input: PartialBulkPurgeHuggingFaceRegistriesInputGQL,
) -> PartialBulkPurgeHuggingFaceRegistriesPayloadGQL:
    payload = await info.context.adapters.huggingface_registry.partial_bulk_purge(
        input.to_pydantic()
    )
    return PartialBulkPurgeHuggingFaceRegistriesPayloadGQL(
        successes=[
            PurgeHuggingFaceRegistryPayloadGQL.from_pydantic(
                purged, extra={"purged_id": to_global_id(HuggingFaceRegistry, purged.entity_id)}
            )
            for purged in payload.successes
        ],
        failed=[PartialBulkFailureGQL.from_pydantic(failure) for failure in payload.failed],
    )
