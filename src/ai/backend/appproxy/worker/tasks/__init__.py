"""Periodic tasks run by the appproxy worker via LocalCron."""

from .heartbeat import WorkerHeartbeatTask

__all__ = [
    "WorkerHeartbeatTask",
]
