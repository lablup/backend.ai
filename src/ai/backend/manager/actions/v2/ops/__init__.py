"""How an action is backed, orthogonal to the target shape it declares.

An action mixing in one of these executes straight against a repository ops spec, so
the domain writes no service method for it.
"""

from .base import (
    BatchPurgeOpsAction,
    BatchUpdateOpsAction,
    BulkCreateOpsAction,
    CreateOpsAction,
    GetOpsAction,
    OpsBackendAction,
    PurgeOpsAction,
    SearchOpsAction,
    UpdateOpsAction,
    UpsertOpsAction,
)
from .result import (
    BatchOpsResult,
    CreatedEntityOpsResult,
    EntitiesOpsResult,
    EntityOpsResult,
)

__all__ = (
    "BatchOpsResult",
    "BatchPurgeOpsAction",
    "BatchUpdateOpsAction",
    "BulkCreateOpsAction",
    "CreateOpsAction",
    "CreatedEntityOpsResult",
    "EntitiesOpsResult",
    "EntityOpsResult",
    "GetOpsAction",
    "OpsBackendAction",
    "PurgeOpsAction",
    "SearchOpsAction",
    "UpdateOpsAction",
    "UpsertOpsAction",
)
