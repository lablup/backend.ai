from __future__ import annotations

import enum


class GPFSJobStatus(enum.StrEnum):
    RUNNING = "RUNNING"
    CANCELLING = "CANCELLING"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class GPFSQuotaType(enum.StrEnum):
    FILESET = "FILESET"
    USER = "USR"
    GROUP = "GRP"
