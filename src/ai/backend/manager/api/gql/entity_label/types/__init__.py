"""Label GQL types.

`inputs` is deliberately absent: it reaches the RBAC scope input, whose package pulls
in the deployment types that import this one. Mutation resolvers import it directly.
"""

from .field import resolve_entity_labels
from .filters import (
    EntityLabelFilterGQL,
    EntityLabelNestedFilterGQL,
    EntityLabelOrderByGQL,
    EntityLabelOrderFieldGQL,
)
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
    # Payload types
    "UpsertEntityLabelPayloadGQL",
    "PurgeEntityLabelPayloadGQL",
    # Shared node field resolver
    "resolve_entity_labels",
]
