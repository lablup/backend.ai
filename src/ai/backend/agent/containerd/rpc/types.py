"""Plain Python values at the client's API; no protobuf type crosses it."""

from __future__ import annotations

import enum
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Final

DEFAULT_CALL_TIMEOUT: Final = 30.0


class TaskState(enum.StrEnum):
    UNKNOWN = "unknown"
    CREATED = "created"
    RUNNING = "running"
    STOPPED = "stopped"
    PAUSED = "paused"
    PAUSING = "pausing"


@dataclass(frozen=True)
class ContainerdClientConfig:
    address: str  # a socket path or a gRPC target such as "unix:///run/containerd/containerd.sock"
    namespace: str
    snapshotter: str
    call_timeout: float = DEFAULT_CALL_TIMEOUT
    create_task_timeout: float = DEFAULT_CALL_TIMEOUT


@dataclass(frozen=True)
class ImageTarget:
    digest: str
    media_type: str


@dataclass(frozen=True)
class MountSpec:
    type: str
    source: str
    options: tuple[str, ...] = ()


@dataclass(frozen=True)
class ContainerRecord:
    id: str
    image: str
    snapshotter: str
    snapshot_key: str
    labels: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class TaskInfo:
    pid: int
    state: TaskState
    exit_status: int


@dataclass(frozen=True)
class RuntimeOptions:
    """A typed runtime options message for Containers.Create, passed through unparsed."""

    type_url: str  # e.g. "runtimeoptions.v1.Options"
    value: bytes  # the serialized message
