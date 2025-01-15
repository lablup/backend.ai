import enum


class ManagerStatus(enum.StrEnum):
    TERMINATED = "terminated"  # deprecated
    PREPARING = "preparing"  # deprecated
    RUNNING = "running"
    FROZEN = "frozen"


class SchedulerEvent(enum.StrEnum):
    SCHEDULE = "schedule"
    CHECK_PRECOND = "check_precondition"
    START_SESSION = "start_session"
    SCALE_SERVICES = "scale_services"
