# The unique identifiers for distributed locks.
# To be used with PostgreSQL advisory locks, the values are defined as integers.
import enum
from typing import Final


class LockID(enum.IntEnum):
    LOCKID_WORKER_LOST = 201
    LOCKID_UNUSED_PORT = 202
    LOCKID_HEALTH_CHECK = 203


REDIS_APPPROXY_DB: Final[int] = 10  # FIXME: move to ai.backend.common.defs
EVENT_DISPATCHER_CONSUMER_GROUP: Final[str] = "appproxy-coordinator"
