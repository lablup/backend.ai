"""Label GQL mutation payload types."""

from __future__ import annotations

from uuid import UUID

import strawberry

from ai.backend.common.dto.manager.v2.entity_label.response import (
    PartialBulkPurgeEntityLabelPayload as PartialBulkPurgeEntityLabelPayloadDTO,
)
from ai.backend.common.dto.manager.v2.entity_label.response import (
    PartialBulkUpsertEntityLabelPayload as PartialBulkUpsertEntityLabelPayloadDTO,
)
from ai.backend.common.dto.manager.v2.entity_label.response import (
    PurgeEntityLabelError as PurgeEntityLabelErrorDTO,
)
from ai.backend.common.dto.manager.v2.entity_label.response import (
    PurgeEntityLabelPayload as PurgeEntityLabelPayloadDTO,
)
from ai.backend.common.dto.manager.v2.entity_label.response import (
    UpsertEntityLabelError as UpsertEntityLabelErrorDTO,
)
from ai.backend.common.dto.manager.v2.entity_label.response import (
    UpsertEntityLabelPayload as UpsertEntityLabelPayloadDTO,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_added_field,
    gql_field,
    gql_pydantic_type,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticOutputMixin

from .node import EntityLabelGQL

__all__ = (
    "PurgeEntityLabelPayloadGQL",
    "PurgeEntityLabelErrorGQL",
    "PartialBulkPurgeEntityLabelPayloadGQL",
    "UpsertEntityLabelPayloadGQL",
    "UpsertEntityLabelErrorGQL",
    "PartialBulkUpsertEntityLabelPayloadGQL",
)


@gql_pydantic_type(
    BackendAIGQLMeta(
        description="Payload returned after putting a label on an entity.",
        added_version="26.9.0",
    ),
    model=UpsertEntityLabelPayloadDTO,
    name="UpsertEntityLabelPayload",
)
class UpsertEntityLabelPayloadGQL(PydanticOutputMixin[UpsertEntityLabelPayloadDTO]):
    label: EntityLabelGQL = gql_field(description="The label as it now stands.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        description=(
            "One item of a bulk label upsert that was not written, named as the request named it."
        ),
        added_version=NEXT_RELEASE_VERSION,
    ),
    model=UpsertEntityLabelErrorDTO,
    name="UpsertEntityLabelError",
)
class UpsertEntityLabelErrorGQL(PydanticOutputMixin[UpsertEntityLabelErrorDTO]):
    entity_type: str = gql_field(description="Type of the entity the failed item targeted.")
    entity_id: UUID = gql_field(description="ID of the entity the failed item targeted.")
    key: str = gql_field(description="The key that was to be put on the entity.")
    message: str = gql_field(description="Reason the item failed.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        description="Partial-success payload for a bulk label upsert, answered per entity.",
        added_version=NEXT_RELEASE_VERSION,
    ),
    model=PartialBulkUpsertEntityLabelPayloadDTO,
    name="PartialBulkUpsertEntityLabelPayload",
)
class PartialBulkUpsertEntityLabelPayloadGQL(
    PydanticOutputMixin[PartialBulkUpsertEntityLabelPayloadDTO]
):
    items: list[EntityLabelGQL] = gql_field(description="The labels put on the entities.")
    failed: list[UpsertEntityLabelErrorGQL] = gql_field(
        description="Per-item failures, each naming the entity and the key it targeted."
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        description="Payload returned after taking a label off an entity.",
        added_version="26.9.0",
    ),
    model=PurgeEntityLabelPayloadDTO,
    name="PurgeEntityLabelPayload",
)
class PurgeEntityLabelPayloadGQL(PydanticOutputMixin[PurgeEntityLabelPayloadDTO]):
    label: EntityLabelGQL = gql_field(
        description="The label taken off the entity.",
        deprecation_reason=f"Deprecated since {NEXT_RELEASE_VERSION}. Use `purgedId` or `fieldId`.",
    )
    purged_id: strawberry.ID = gql_added_field(
        BackendAIGQLMeta(
            added_version=NEXT_RELEASE_VERSION, description="Global ID of the purged entity label."
        ),
    )
    field_id: UUID = gql_added_field(
        BackendAIGQLMeta(
            added_version=NEXT_RELEASE_VERSION, description="UUID of the purged entity label."
        ),
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        description="One label a bulk purge could not take off.",
        added_version=NEXT_RELEASE_VERSION,
    ),
    model=PurgeEntityLabelErrorDTO,
    name="PurgeEntityLabelError",
)
class PurgeEntityLabelErrorGQL(PydanticOutputMixin[PurgeEntityLabelErrorDTO]):
    id: UUID = gql_field(description="ID of the label the failed item targeted.")
    message: str = gql_field(description="Reason the item failed.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        description="Partial-success payload for a bulk label purge, answered per label.",
        added_version=NEXT_RELEASE_VERSION,
    ),
    model=PartialBulkPurgeEntityLabelPayloadDTO,
    name="PartialBulkPurgeEntityLabelPayload",
)
class PartialBulkPurgeEntityLabelPayloadGQL(
    PydanticOutputMixin[PartialBulkPurgeEntityLabelPayloadDTO]
):
    successes: list[UUID] = gql_field(description="Ids of the labels taken off.")
    failed: list[PurgeEntityLabelErrorGQL] = gql_field(
        description="Per-label failures, each naming the label it targeted."
    )
