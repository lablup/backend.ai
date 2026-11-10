"""Label DTOs v2 for Manager API."""

from ai.backend.common.dto.manager.v2.entity_label.request import (
    EntityLabelFilter,
    EntityLabelNestedFilter,
    EntityLabelOrder,
    PartialBulkPurgeEntityLabelInput,
    PartialBulkUpsertEntityLabelInput,
    SearchEntityLabelsInput,
    UpsertEntityLabelInput,
)
from ai.backend.common.dto.manager.v2.entity_label.response import (
    EntityLabelNode,
    PartialBulkPurgeEntityLabelPayload,
    PartialBulkUpsertEntityLabelPayload,
    PurgeEntityLabelError,
    PurgeEntityLabelPayload,
    SearchEntityLabelsPayload,
    UpsertEntityLabelError,
    UpsertEntityLabelPayload,
)
from ai.backend.common.dto.manager.v2.entity_label.types import (
    EntityLabelOrderField,
    OrderDirection,
)

__all__ = (
    "UpsertEntityLabelInput",
    "UpsertEntityLabelPayload",
    "UpsertEntityLabelError",
    "PartialBulkUpsertEntityLabelInput",
    "PartialBulkUpsertEntityLabelPayload",
    "EntityLabelFilter",
    "EntityLabelNestedFilter",
    "EntityLabelNode",
    "EntityLabelOrder",
    "EntityLabelOrderField",
    "OrderDirection",
    "PurgeEntityLabelPayload",
    "PurgeEntityLabelError",
    "PartialBulkPurgeEntityLabelInput",
    "PartialBulkPurgeEntityLabelPayload",
    "SearchEntityLabelsInput",
    "SearchEntityLabelsPayload",
)
