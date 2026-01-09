import re
from enum import StrEnum
from typing import Final

# Redis database IDs depending on purposes
REDIS_STATISTICS_DB: Final = 0
REDIS_RATE_LIMIT_DB: Final = 1
REDIS_LIVE_DB: Final = 2
REDIS_IMAGE_DB: Final = 3
REDIS_STREAM_DB: Final = 4
REDIS_STREAM_LOCK: Final = 5
REDIS_CONTAINER_LOG: Final = 6
REDIS_BGTASK_DB: Final = 7


class RedisRole(StrEnum):
    STATISTICS = "statistics"
    RATE_LIMIT = "rate_limit"
    LIVE = "live"
    IMAGE = "image"
    STREAM = "stream"
    STREAM_LOCK = "stream_lock"
    CONTAINER_LOG = "container_log"
    BGTASK = "bgtask"


DEFAULT_FILE_IO_TIMEOUT: Final = 10

_RESERVED_VFOLDER_PATTERNS = [r"^\.[a-z0-9]+rc$", r"^\.[a-z0-9]+_profile$"]
RESERVED_VFOLDERS = [
    ".terminfo",
    ".jupyter",
    ".tmux.conf",
    ".ssh",
    "/bin",
    "/boot",
    "/dev",
    "/etc",
    "/lib",
    "/lib64",
    "/media",
    "/mnt",
    "/opt",
    "/proc",
    "/root",
    "/run",
    "/sbin",
    "/srv",
    "/sys",
    "/tmp",
    "/usr",
    "/var",
    "/home",
]
RESERVED_VFOLDER_PATTERNS = [re.compile(x) for x in _RESERVED_VFOLDER_PATTERNS]
API_VFOLDER_LENGTH_LIMIT: Final[int] = 64
MODEL_VFOLDER_LENGTH_LIMIT: Final[int] = 128

DEFAULT_VFOLDER_PERMISSION_MODE: Final[int] = 0o755
VFOLDER_GROUP_PERMISSION_MODE: Final[int] = 0o775

DEFAULT_DOMAIN_NAME: Final[str] = "default"

NOOP_STORAGE_VOLUME_NAME: Final[str] = "noop"
NOOP_STORAGE_BACKEND_TYPE: Final[str] = "noop"

UNKNOWN_CONTAINER_ID: Final[str] = "unknown"
