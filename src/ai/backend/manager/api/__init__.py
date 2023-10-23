import enum


class ManagerStatus(str, enum.Enum):
    TERMINATED = "terminated"  # deprecated
    PREPARING = "preparing"  # deprecated
    RUNNING = "running"
    FROZEN = "frozen"


class SchedulerEvent(str, enum.Enum):
    SCHEDULE = "schedule"
    PREPARE = "prepare"
    SCALE_SERVICES = "scale_services"
