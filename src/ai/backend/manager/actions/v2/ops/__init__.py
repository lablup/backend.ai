"""How an action is backed, orthogonal to the target shape it declares.

An action mixing in one of these executes straight against a repository ops spec, so
the domain writes no service method for it.
"""

from .base import (
    BatchPurgeOpsAction,
    BatchUpdateOpsAction,
    BulkCreateOpsAction,
    BulkPurgeOpsAction,
    BulkUpdateOpsAction,
    CreateOpsAction,
    GetOpsAction,
    LookupOpsAction,
    OpsBackendAction,
    PurgeOpsAction,
    SearchOpsAction,
    UpdateOpsAction,
    UpsertOpsAction,
)
from .result import (
    BatchOpsResult,
    BulkOpsResult,
    CreatedEntityOpsResult,
    EntitiesOpsResult,
    EntityOpsResult,
    LookupOpsResult,
)

__all__ = (
    "BatchOpsResult",
    "BatchPurgeOpsAction",
    "BatchUpdateOpsAction",
    "BulkCreateOpsAction",
    "BulkOpsResult",
    "BulkPurgeOpsAction",
    "BulkUpdateOpsAction",
    "CreateOpsAction",
    "CreatedEntityOpsResult",
    "EntitiesOpsResult",
    "EntityOpsResult",
    "LookupOpsAction",
    "LookupOpsResult",
    "GetOpsAction",
    "OpsBackendAction",
    "PurgeOpsAction",
    "SearchOpsAction",
    "UpdateOpsAction",
    "UpsertOpsAction",
)
