"""Generic services for ops-backed actions, replacing per-domain pass-through methods."""

from .service import (
    BatchPurgeService,
    BatchUpdateService,
    BulkCreateService,
    CreateService,
    DeleteService,
    GetService,
    LookupService,
    PurgeService,
    SearchService,
    UpdateService,
    UpsertService,
)

__all__ = (
    "BatchPurgeService",
    "BatchUpdateService",
    "BulkCreateService",
    "CreateService",
    "DeleteService",
    "GetService",
    "LookupService",
    "PurgeService",
    "SearchService",
    "UpdateService",
    "UpsertService",
)
