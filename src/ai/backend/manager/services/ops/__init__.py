"""Generic services for ops-backed actions, replacing per-domain pass-through methods."""

from .service import (
    BatchPurgeService,
    BatchUpdateService,
    BulkCreateService,
    BulkDeleteService,
    BulkPurgeService,
    BulkUpdateService,
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
    "BulkDeleteService",
    "BulkPurgeService",
    "BulkUpdateService",
    "CreateService",
    "DeleteService",
    "GetService",
    "LookupService",
    "PurgeService",
    "SearchService",
    "UpdateService",
    "UpsertService",
)
