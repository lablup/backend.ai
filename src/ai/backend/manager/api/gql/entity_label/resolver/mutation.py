"""Label GQL mutation resolvers."""

from __future__ import annotations

from strawberry import ID, Info

from ai.backend.common.data.entity.entity_label import EntityLabelID
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.base import parse_uuid
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_mutation,
)
from ai.backend.manager.api.gql.entity_label.types.inputs import (
    PartialBulkPurgeEntityLabelInputGQL,
    PartialBulkUpsertEntityLabelInputGQL,
    UpsertEntityLabelInputGQL,
)
from ai.backend.manager.api.gql.entity_label.types.payloads import (
    PartialBulkPurgeEntityLabelPayloadGQL,
    PartialBulkUpsertEntityLabelPayloadGQL,
    PurgeEntityLabelPayloadGQL,
    UpsertEntityLabelPayloadGQL,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext


@gql_mutation(
    BackendAIGQLMeta(
        description=(
            "Set one key on an entity, replacing the value it carries. Reachable by any "
            "caller RBAC authorizes to write the entity."
        ),
        added_version="26.9.0",
    )
)
async def upsert_entity_label(
    info: Info[StrawberryGQLContext],
    input: UpsertEntityLabelInputGQL,
) -> UpsertEntityLabelPayloadGQL | None:
    payload = await info.context.adapters.entity_label.upsert(input.to_pydantic())
    return UpsertEntityLabelPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        description=(
            "Set keys on several entities in one call, answering per entity. An entity "
            "the caller may not write is one failed item; the rest are written."
        ),
        added_version=NEXT_RELEASE_VERSION,
    )
)
async def partial_bulk_upsert_entity_label(
    info: Info[StrawberryGQLContext],
    input: PartialBulkUpsertEntityLabelInputGQL,
) -> PartialBulkUpsertEntityLabelPayloadGQL | None:
    payload = await info.context.adapters.entity_label.partial_bulk_upsert(input.to_pydantic())
    return PartialBulkUpsertEntityLabelPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        description=(
            "Take one label off, named by its own id. Which entity answers for it is read "
            "from the row before the delete runs."
        ),
        added_version="26.9.0",
    )
)
async def purge_entity_label(
    info: Info[StrawberryGQLContext],
    id: ID,
) -> PurgeEntityLabelPayloadGQL | None:
    payload = await info.context.adapters.entity_label.purge(EntityLabelID(parse_uuid(id)))
    return PurgeEntityLabelPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        description=(
            "Take several labels off in one call, each named by its own id and answered "
            "for on its own. A label that is gone or on an entity the caller may not "
            "write is one failed item; the rest are taken off."
        ),
        added_version=NEXT_RELEASE_VERSION,
    )
)
async def partial_bulk_purge_entity_label(
    info: Info[StrawberryGQLContext],
    input: PartialBulkPurgeEntityLabelInputGQL,
) -> PartialBulkPurgeEntityLabelPayloadGQL | None:
    payload = await info.context.adapters.entity_label.partial_bulk_purge(input.to_pydantic())
    return PartialBulkPurgeEntityLabelPayloadGQL.from_pydantic(payload)
