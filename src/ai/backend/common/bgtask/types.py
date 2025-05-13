import enum


class BgtaskStatus(enum.StrEnum):
    STARTED = "bgtask_started"
    DONE = "bgtask_done"
    CANCELLED = "bgtask_cancelled"
    FAILED = "bgtask_failed"
    PARTIAL_SUCCESS = "bgtask_partial_success"

    def finished(self) -> bool:
        return self in {self.DONE, self.CANCELLED, self.FAILED, self.PARTIAL_SUCCESS}
