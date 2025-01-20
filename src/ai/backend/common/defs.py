import re
from typing import Final

# Redis database IDs depending on purposes
REDIS_STAT_DB: Final = 0
REDIS_RLIM_DB: Final = 1
REDIS_LIVE_DB: Final = 2
REDIS_IMAGE_DB: Final = 3
REDIS_STREAM_DB: Final = 4
REDIS_STREAM_LOCK: Final = 5


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
