"""How an action is backed, orthogonal to the target shape it declares.

An action mixing in one of these executes straight against a repository ops spec, so
the domain writes no service method for it.
"""

from .base import (
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
    EntityOpsResult,
)

__all__ = (
    "BatchOpsResult",
    "CreateOpsAction",
    "CreatedEntityOpsResult",
    "EntityOpsResult",
    "GetOpsAction",
    "OpsBackendAction",
    "PurgeOpsAction",
    "SearchOpsAction",
    "UpdateOpsAction",
    "UpsertOpsAction",
)
