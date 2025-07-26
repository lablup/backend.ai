from ai.backend.common.types import ContainerStatus

ACTIVE_STATUS_SET = frozenset((
    ContainerStatus.RUNNING,
    ContainerStatus.RESTARTING,
    ContainerStatus.PAUSED,
))
