import enum


class ManagerStatus(enum.StrEnum):
    TERMINATED = "terminated"  # deprecated
    PREPARING = "preparing"  # deprecated
    RUNNING = "running"
    FROZEN = "frozen"


class SchedulerEvent(enum.StrEnum):
    SCHEDULE = "schedule"
    PREPARE = "prepare"
    CHECK_READINESS = "check_readiness"
    START_SESSION = "start_session"
    SCALE_SERVICES = "scale_services"
