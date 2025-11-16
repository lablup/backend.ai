from __future__ import annotations

from .abc import HealthChecker
from .checkers import (
    EtcdHealthChecker,
    HttpHealthChecker,
    ValkeyHealthChecker,
)
from .exceptions import (
    HealthCheckerAlreadyRegistered,
    HealthCheckerNotFound,
    HealthCheckError,
)
from .probe import HealthProbe, HealthProbeOptions, RegisteredChecker
from .types import (
    AGENT,
    APPPROXY,
    CID_DOCKER,
    CID_ETCD,
    CID_POSTGRES,
    CID_REDIS_ARTIFACT,
    CID_REDIS_BGTASK,
    CID_REDIS_CONTAINER_LOG,
    CID_REDIS_CORE_LIVE,
    CID_REDIS_IMAGE,
    CID_REDIS_LIVE,
    CID_REDIS_SCHEDULE,
    CID_REDIS_SESSION,
    CID_REDIS_STAT,
    CID_REDIS_STREAM,
    DATABASE,
    ETCD,
    MANAGER,
    REDIS,
    STORAGE_PROXY,
    AllHealthCheckResults,
    ComponentId,
    HealthCheckResult,
    HealthCheckStatus,
    ServiceGroup,
)

__all__ = [
    # ABC
    "HealthChecker",
    # Checkers
    "EtcdHealthChecker",
    "HttpHealthChecker",
    "ValkeyHealthChecker",
    # Exceptions
    "HealthCheckError",
    "HealthCheckerAlreadyRegistered",
    "HealthCheckerNotFound",
    # Types
    "ServiceGroup",
    "ComponentId",
    "HealthCheckResult",
    "HealthCheckStatus",
    "AllHealthCheckResults",
    # Built-in ServiceGroups
    "MANAGER",
    "AGENT",
    "STORAGE_PROXY",
    "APPPROXY",
    "DATABASE",
    "ETCD",
    "REDIS",
    # Built-in ComponentIds
    "CID_POSTGRES",
    "CID_REDIS_ARTIFACT",
    "CID_REDIS_CONTAINER_LOG",
    "CID_REDIS_LIVE",
    "CID_REDIS_STAT",
    "CID_REDIS_IMAGE",
    "CID_REDIS_STREAM",
    "CID_REDIS_SCHEDULE",
    "CID_REDIS_BGTASK",
    "CID_REDIS_SESSION",
    "CID_REDIS_CORE_LIVE",
    "CID_ETCD",
    "CID_DOCKER",
    # Probe
    "HealthProbe",
    "HealthProbeOptions",
    "RegisteredChecker",
]
