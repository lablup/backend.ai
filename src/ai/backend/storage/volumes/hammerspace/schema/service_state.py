import enum


class ServiceState(enum.StrEnum):
    UNKNOWN = "UNKNOWN"
    INITIALIZING = "INITIALIZING"
    RUNNING = "RUNNING"
    FAILED = "FAILED"
    STOPPED = "STOPPED"
