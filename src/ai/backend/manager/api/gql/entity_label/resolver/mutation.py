"""Label GQL mutation resolvers."""

from __future__ import annotations

from uuid import UUID

from strawberry import ID, Info

from ai.backend.common.data.entity.entity_label import EntityLabelID
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_mutation,
)
from ai.backend.manager.api.gql.entity_label.types import (
    PurgeEntityLabelPayloadGQL,
    UpsertEntityLabelInputGQL,
    UpsertEntityLabelPayloadGQL,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext


@gql_mutation(
    BackendAIGQLMeta(
        description=(
            "Set one key on an entity, replacing the value it carries. Reachable by any "
            "caller RBAC authorizes to write the entity."
        ),
        added_version=NEXT_RELEASE_VERSION,
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
            "Take one label off, named by its own id. Which entity answers for it is read "
            "from the row before the delete runs."
        ),
        added_version=NEXT_RELEASE_VERSION,
    )
)
async def purge_entity_label(
    info: Info[StrawberryGQLContext],
    id: ID,
) -> PurgeEntityLabelPayloadGQL | None:
    payload = await info.context.adapters.entity_label.purge(EntityLabelID(UUID(str(id))))
    return PurgeEntityLabelPayloadGQL.from_pydantic(payload)
