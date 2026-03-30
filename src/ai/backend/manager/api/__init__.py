import enum


class ManagerStatus(enum.StrEnum):
    TERMINATED = "terminated"  # deprecated
    PREPARING = "preparing"  # deprecated
    RUNNING = "running"
    FROZEN = "frozen"
