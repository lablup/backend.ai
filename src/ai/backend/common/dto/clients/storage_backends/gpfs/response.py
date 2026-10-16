from __future__ import annotations

from typing import Any

from pydantic import ConfigDict, Field

from ai.backend.common.dto.clients.storage_backends.gpfs.types import (
    GPFSJobStatus,
)
from ai.backend.common.types import BackendAISchema


class GPFSFilesystemBlock(BackendAISchema):
    pools: str | None = None
    disks: str | None = None
    blockSize: int | None = None
    metaDataBlockSize: int | None = None
    indirectBlockSize: int | None = None
    minFragmentSize: int | None = None
    inodeSize: int | None = None
    logfileSize: int | None = None
    writeCacheThreshold: int | None = None


class GPFSFilesystemMount(BackendAISchema):
    mountPoint: str | None = None
    automaticMountOption: str | None = None
    additionalMountOptions: str | None = None
    mountPriority: int | None = None
    driveLetter: str | None = None
    remoteDeviceName: str | None = None
    readOnly: bool | None = None
    nodesMountedReadWrite: list[str] | None = None
    nodesMountedReadOnly: list[str] | None = None
    nodesMountedInternally: list[str] | None = None
    status: str | None = None


class GPFSFilesystemReplication(BackendAISchema):
    defaultMetadataReplicas: int | None = None
    maxMetadataReplicas: int | None = None
    defaultDataReplicas: int | None = None
    maxDataReplicas: int | None = None
    strictReplication: str | None = None
    logReplicas: int | None = None


class GPFSFilesystemQuota(BackendAISchema):
    quotasAccountingEnabled: str | None = None
    quotasEnforced: str | None = None
    defaultQuotasEnabled: str | None = None
    perfilesetQuotas: bool | None = None
    filesetdfEnabled: bool | None = None


class GPFSFilesystemSettings(BackendAISchema):
    blockAllocationType: str | None = None
    fileLockingSemantics: str | None = None
    aclSemantics: str | None = None
    numNodes: int | None = None
    dmapiEnabled: bool | None = None
    exactMTime: bool | None = None
    suppressATime: str | None = None
    fastEAEnabled: bool | None = None
    encryption: bool | None = None
    maxNumberOfInodes: int | None = None
    is4KAligned: bool | None = None
    rapidRepairEnabled: bool | None = None
    stripeMethod: str | None = None
    stripedLogs: bool | None = None
    fileAuditLogEnabled: bool | None = None


class GPFSFileAuditLogConfig(BackendAISchema):
    auditFilesetDeviceName: str | None = None
    auditFilesetName: str | None = None
    auditRetention: int | None = None
    topicGenNum: int | None = None
    eventTypes: str | None = None


class GPFSFilesystem(BackendAISchema):
    oid: int | None = None
    uuid: str | None = None
    name: str | None = None
    version: str | None = None
    type: str | None = None
    createTime: str | None = None
    block: GPFSFilesystemBlock | None = None
    mount: GPFSFilesystemMount | None = None
    replication: GPFSFilesystemReplication | None = None
    quota: GPFSFilesystemQuota | None = None
    settings: GPFSFilesystemSettings | None = None
    fileAuditLogConfig: GPFSFileAuditLogConfig | None = None


class GPFSQuota(BackendAISchema):
    quotaId: int | None = None
    filesystemName: str | None = None
    quotaType: str | None = None
    objectName: str | None = None
    objectId: int | None = None
    blockUsage: int | None = None
    blockQuota: int | None = None
    blockLimit: int | None = None
    blockInDoubt: int | None = None
    blockGrace: str | None = None
    filesUsage: int | None = None
    filesQuota: int | None = None
    filesLimit: int | None = None
    filesInDoubt: int | None = None
    filesGrace: str | None = None
    isDefaultQuota: bool | None = None


class GPFSStoragePoolUsage(BackendAISchema):
    storagePoolName: str
    filesystemName: str
    totalDataInKB: int | None = None
    freeDataInKB: int | None = None
    totalMetaInKB: int | None = None
    freeMetaInKB: int | None = None


class GPFSSystemHealthState(BackendAISchema):
    oid: int | None = None
    component: str | None = None
    reportingNode: str | None = None
    activeSince: str | None = None
    entityType: str | None = None
    entityName: str | None = None
    parentName: str | None = None
    state: str | None = None
    reasons: list[str] | None = None


class GPFSDisk(BackendAISchema):
    name: str
    fileSystem: str
    failureGroup: str | None = None
    type: str | None = None
    storagePool: str | None = None
    status: str | None = None
    availability: str | None = None
    quorumDisk: bool | None = None
    remarks: str | None = None
    size: int | None = None
    availableBlocks: int | None = None
    availableFragments: int | None = None
    nsdServers: str | None = None
    nsdVolumeId: str | None = None


class GPFSJobResult(BackendAISchema):
    commands: list[str] | None = None
    progress: list[str] | None = None
    exitCode: int | None = None
    stderr: list[str] | None = None
    stdout: list[str] | None = None


class GPFSJobRequest(BackendAISchema):
    type: str | None = None
    url: str | None = None
    data: Any | None = None


class GPFSJob(BackendAISchema):
    jobId: int
    status: GPFSJobStatus
    result: GPFSJobResult | None = None
    request: GPFSJobRequest | None = None
    submitted: str | None = None
    completed: str | None = None
    runtime: int | None = None
    pids: list[int] | None = None


class GPFSClusterInfo(BackendAISchema):
    model_config = ConfigDict(extra="allow")


class GPFSPerfmonRow(BackendAISchema):
    model_config = ConfigDict(extra="allow")

    values: list[float | None] = Field(default_factory=list)


class GPFSPerfmonData(BackendAISchema):
    model_config = ConfigDict(extra="allow")

    rows: list[GPFSPerfmonRow] = Field(default_factory=list)


class GPFSMetric(BackendAISchema):
    model_config = ConfigDict(extra="allow")

    performanceData: GPFSPerfmonData | None = None


class GPFSHealthCheck(BackendAISchema):
    text: str


class GPFSNode(BackendAISchema):
    adminNodeName: str
