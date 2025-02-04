import enum
from dataclasses import dataclass
from typing import Any, List, Optional

from dataclasses_json import DataClassJsonMixin


@dataclass
class GPFSFilesystemBlock(DataClassJsonMixin):
    pools: Optional[str]
    disks: Optional[str]
    blockSize: Optional[int]
    metaDataBlockSize: Optional[int]
    indirectBlockSize: Optional[int]
    minFragmentSize: Optional[int]
    inodeSize: Optional[int]
    logfileSize: Optional[int]
    writeCacheThreshold: Optional[int]


@dataclass
class GPFSFilesystemMount(DataClassJsonMixin):
    mountPoint: Optional[str]
    automaticMountOption: Optional[str]
    additionalMountOptions: Optional[str]
    mountPriority: Optional[int]
    driveLetter: Optional[str]
    remoteDeviceName: Optional[str]
    readOnly: Optional[bool]
    nodesMountedReadWrite: Optional[List[str]]
    nodesMountedReadOnly: Optional[List[str]]
    nodesMountedInternally: Optional[List[str]]
    status: Optional[str]


@dataclass
class GPFSFilesystemReplication(DataClassJsonMixin):
    defaultMetadataReplicas: Optional[int]
    maxMetadataReplicas: Optional[int]
    defaultDataReplicas: Optional[int]
    maxDataReplicas: Optional[int]
    strictReplication: Optional[str]
    logReplicas: Optional[int]


@dataclass
class GPFSFilesystemQuota(DataClassJsonMixin):
    quotasAccountingEnabled: Optional[str]
    quotasEnforced: Optional[str]
    defaultQuotasEnabled: Optional[str]
    perfilesetQuotas: Optional[bool]
    filesetdfEnabled: Optional[bool]


@dataclass
class GPFSFilesystemSettings(DataClassJsonMixin):
    blockAllocationType: Optional[str]
    fileLockingSemantics: Optional[str]
    aclSemantics: Optional[str]
    numNodes: Optional[int]
    dmapiEnabled: Optional[bool]
    exactMTime: Optional[bool]
    suppressATime: Optional[str]
    fastEAEnabled: Optional[bool]
    encryption: Optional[bool]
    maxNumberOfInodes: Optional[int]
    is4KAligned: Optional[bool]
    rapidRepairEnabled: Optional[bool]
    stripeMethod: Optional[str]
    stripedLogs: Optional[bool]
    fileAuditLogEnabled: Optional[bool]


@dataclass
class GPFSFileAuditLogConfig(DataClassJsonMixin):
    auditFilesetDeviceName: Optional[str]
    auditFilesetName: Optional[str]
    auditRetention: Optional[int]
    topicGenNum: Optional[int]
    eventTypes: Optional[str]


@dataclass
class GPFSFilesystem(DataClassJsonMixin):
    oid: Optional[int]
    uuid: Optional[str]
    name: Optional[str]
    version: Optional[str]
    type: Optional[str]
    createTime: Optional[str]
    block: Optional[GPFSFilesystemBlock]
    mount: Optional[GPFSFilesystemMount]
    replication: Optional[GPFSFilesystemReplication]
    quota: Optional[GPFSFilesystemQuota]
    settings: Optional[GPFSFilesystemSettings]
    fileAuditLogConfig: Optional[GPFSFileAuditLogConfig]


@dataclass
class GPFSQuota(DataClassJsonMixin):
    quotaId: Optional[int]
    filesystemName: Optional[str]
    quotaType: Optional[str]
    objectName: Optional[str]  # This represents fileset name you query quota of filesets.
    objectId: Optional[int]
    blockUsage: Optional[int]
    blockQuota: Optional[int]
    blockLimit: Optional[int]
    blockInDoubt: Optional[int]
    blockGrace: Optional[str]
    filesUsage: Optional[int]
    filesQuota: Optional[int]
    filesLimit: Optional[int]
    filesInDoubt: Optional[int]
    filesGrace: Optional[str]
    isDefaultQuota: Optional[bool]


@dataclass
class GPFSStoragePoolUsage(DataClassJsonMixin):
    storagePoolName: str
    filesystemName: str
    totalDataInKB: Optional[int] = None
    freeDataInKB: Optional[int] = None
    totalMetaInKB: Optional[int] = None
    freeMetaInKB: Optional[int] = None


@dataclass
class GPFSSystemHealthState(DataClassJsonMixin):
    oid: Optional[int]
    component: Optional[str]
    reportingNode: Optional[str]
    activeSince: Optional[str]
    entityType: Optional[str]
    entityName: Optional[str]
    parentName: Optional[str]
    state: Optional[str]
    reasons: Optional[List[str]]


@dataclass
class GPFSDisk(DataClassJsonMixin):
    name: str
    fileSystem: str
    failureGroup: Optional[str] = None
    type: Optional[str] = None
    storagePool: Optional[str] = None
    status: Optional[str] = None
    availability: Optional[str] = None
    quorumDisk: Optional[bool] = None
    remarks: Optional[str] = None
    size: Optional[int] = None
    availableBlocks: Optional[int] = None
    availableFragments: Optional[int] = None
    nsdServers: Optional[str] = None
    nsdVolumeId: Optional[str] = None


@dataclass
class GPFSJobResult(DataClassJsonMixin):
    commands: Optional[List[str]] = None
    progress: Optional[List[str]] = None
    exitCode: Optional[int] = None
    stderr: Optional[List[str]] = None
    stdout: Optional[List[str]] = None


@dataclass
class GPFSJobRequest(DataClassJsonMixin):
    type: Optional[str] = None
    url: Optional[str] = None
    data: Optional[Any] = None


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
    result: Optional[GPFSJobResult] = None
    request: Optional[GPFSJobRequest] = None
    submitted: Optional[str] = None
    completed: Optional[str] = None
    runtime: Optional[int] = None
    pids: Optional[List[int]] = None


class GPFSQuotaType(enum.StrEnum):
    FILESET = "FILESET"
    USER = "USR"
    GROUP = "GRP"
