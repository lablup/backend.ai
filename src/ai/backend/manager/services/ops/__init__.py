"""Generic services for ops-backed actions, replacing per-domain pass-through methods."""

from .service import (
    CreateService,
    DeleteService,
    GetService,
    PurgeService,
    SearchService,
    UpdateService,
    UpsertService,
)

__all__ = (
    "CreateService",
    "DeleteService",
    "GetService",
    "PurgeService",
    "SearchService",
    "UpdateService",
    "UpsertService",
)
