import enum
from dataclasses import dataclass
from typing import Any

from dataclasses_json import DataClassJsonMixin


@dataclass
class GPFSFilesystemBlock(DataClassJsonMixin):
    pools: str | None
    disks: str | None
    blockSize: int | None
    metaDataBlockSize: int | None
    indirectBlockSize: int | None
    minFragmentSize: int | None
    inodeSize: int | None
    logfileSize: int | None
    writeCacheThreshold: int | None


@dataclass
class GPFSFilesystemMount(DataClassJsonMixin):
    mountPoint: str | None
    automaticMountOption: str | None
    additionalMountOptions: str | None
    mountPriority: int | None
    driveLetter: str | None
    remoteDeviceName: str | None
    readOnly: bool | None
    nodesMountedReadWrite: list[str] | None
    nodesMountedReadOnly: list[str] | None
    nodesMountedInternally: list[str] | None
    status: str | None


@dataclass
class GPFSFilesystemReplication(DataClassJsonMixin):
    defaultMetadataReplicas: int | None
    maxMetadataReplicas: int | None
    defaultDataReplicas: int | None
    maxDataReplicas: int | None
    strictReplication: str | None
    logReplicas: int | None


@dataclass
class GPFSFilesystemQuota(DataClassJsonMixin):
    quotasAccountingEnabled: str | None
    quotasEnforced: str | None
    defaultQuotasEnabled: str | None
    perfilesetQuotas: bool | None
    filesetdfEnabled: bool | None


@dataclass
class GPFSFilesystemSettings(DataClassJsonMixin):
    blockAllocationType: str | None
    fileLockingSemantics: str | None
    aclSemantics: str | None
    numNodes: int | None
    dmapiEnabled: bool | None
    exactMTime: bool | None
    suppressATime: str | None
    fastEAEnabled: bool | None
    encryption: bool | None
    maxNumberOfInodes: int | None
    is4KAligned: bool | None
    rapidRepairEnabled: bool | None
    stripeMethod: str | None
    stripedLogs: bool | None
    fileAuditLogEnabled: bool | None


@dataclass
class GPFSFileAuditLogConfig(DataClassJsonMixin):
    auditFilesetDeviceName: str | None
    auditFilesetName: str | None
    auditRetention: int | None
    topicGenNum: int | None
    eventTypes: str | None


@dataclass
class GPFSFilesystem(DataClassJsonMixin):
    oid: int | None
    uuid: str | None
    name: str | None
    version: str | None
    type: str | None
    createTime: str | None
    block: GPFSFilesystemBlock | None
    mount: GPFSFilesystemMount | None
    replication: GPFSFilesystemReplication | None
    quota: GPFSFilesystemQuota | None
    settings: GPFSFilesystemSettings | None
    fileAuditLogConfig: GPFSFileAuditLogConfig | None


@dataclass
class GPFSQuota(DataClassJsonMixin):
    quotaId: int | None
    filesystemName: str | None
    quotaType: str | None
    objectName: str | None  # This represents fileset name you query quota of filesets.
    objectId: int | None
    blockUsage: int | None
    blockQuota: int | None
    blockLimit: int | None
    blockInDoubt: int | None
    blockGrace: str | None
    filesUsage: int | None
    filesQuota: int | None
    filesLimit: int | None
    filesInDoubt: int | None
    filesGrace: str | None
    isDefaultQuota: bool | None


@dataclass
class GPFSStoragePoolUsage(DataClassJsonMixin):
    storagePoolName: str
    filesystemName: str
    totalDataInKB: int | None = None
    freeDataInKB: int | None = None
    totalMetaInKB: int | None = None
    freeMetaInKB: int | None = None


@dataclass
class GPFSSystemHealthState(DataClassJsonMixin):
    oid: int | None
    component: str | None
    reportingNode: str | None
    activeSince: str | None
    entityType: str | None
    entityName: str | None
    parentName: str | None
    state: str | None
    reasons: list[str] | None


@dataclass
class GPFSDisk(DataClassJsonMixin):
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


@dataclass
class GPFSJobResult(DataClassJsonMixin):
    commands: list[str] | None = None
    progress: list[str] | None = None
    exitCode: int | None = None
    stderr: list[str] | None = None
    stdout: list[str] | None = None


@dataclass
class GPFSJobRequest(DataClassJsonMixin):
    type: str | None = None
    url: str | None = None
    data: Any | None = None


class GPFSJobStatus(enum.StrEnum):
    RUNNING = "RUNNING"
    CANCELLING = "CANCELLING"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


@dataclass
class GPFSJob(DataClassJsonMixin):
    jobId: int
    status: GPFSJobStatus
    result: GPFSJobResult | None = None
    request: GPFSJobRequest | None = None
    submitted: str | None = None
    completed: str | None = None
    runtime: int | None = None
    pids: list[int] | None = None


class GPFSQuotaType(enum.StrEnum):
    FILESET = "FILESET"
    USER = "USR"
    GROUP = "GRP"
