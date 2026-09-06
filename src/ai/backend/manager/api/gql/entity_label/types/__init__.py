"""Label GQL types."""

from .field import resolve_entity_labels
from .filters import (
    EntityLabelFilterGQL,
    EntityLabelNestedFilterGQL,
    EntityLabelOrderByGQL,
    EntityLabelOrderFieldGQL,
)
from .inputs import UpsertEntityLabelInputGQL
from .node import (
    EntityLabelConnection,
    EntityLabelEdge,
    EntityLabelGQL,
)
from .payloads import (
    PurgeEntityLabelPayloadGQL,
    UpsertEntityLabelPayloadGQL,
)

__all__ = [
    # Node / Connection types
    "EntityLabelGQL",
    "EntityLabelEdge",
    "EntityLabelConnection",
    # Filter / OrderBy types
    "EntityLabelFilterGQL",
    "EntityLabelNestedFilterGQL",
    "EntityLabelOrderByGQL",
    "EntityLabelOrderFieldGQL",
    # Input types
    "UpsertEntityLabelInputGQL",
    # Payload types
    "UpsertEntityLabelPayloadGQL",
    "PurgeEntityLabelPayloadGQL",
    # Shared node field resolver
    "resolve_entity_labels",
]
