from __future__ import annotations

from ai.backend.common.dto.clients.storage_backends.gpfs.types import (
    GPFSQuotaType,
)
from ai.backend.common.types import BackendAISchema


class GPFSSetQuotaRequest(BackendAISchema):
    operationType: str = "setQuota"
    quotaType: GPFSQuotaType = GPFSQuotaType.FILESET
    objectName: str
    blockSoftLimit: str
    blockHardLimit: str


class GPFSCreateFilesetRequest(BackendAISchema):
    filesetName: str
    owner: str | None = None
    permissions: int | None = None
    path: str | None = None


class GPFSCopyFolderRequest(BackendAISchema):
    targetFilesystem: str
    targetFileset: str = "fset1"
    targetPath: str


class GPFSFilesetQuotasQuery(BackendAISchema):
    filter: str


class GPFSMetricQuery(BackendAISchema):
    query: str
