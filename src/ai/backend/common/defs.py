<<<<<<< HEAD
import re
=======
>>>>>>> 6dd7f0242 (rename and relocate constants and variables)
from decimal import Decimal
from typing import Final

# Redis database IDs depending on purposes
REDIS_STAT_DB: Final = 0
REDIS_RLIM_DB: Final = 1
REDIS_LIVE_DB: Final = 2
REDIS_IMAGE_DB: Final = 3
REDIS_STREAM_DB: Final = 4
REDIS_STREAM_LOCK: Final = 5


DEFAULT_FILE_IO_TIMEOUT: Final = 10

<<<<<<< HEAD
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

DEFAULT_SHARED_MEMORY_SIZE: Final[str] = "64m"
DEFAULT_ALLOWED_MAX_SHMEM_RATIO: Final[Decimal] = Decimal(1.0)
SHMEM_RATIO_KEY: Final[str] = "resources/shmem-mem-ratio"
=======

DEFAULT_SHARED_MEMORY_SIZE: Final = "64m"
DEFAULT_ALLOWED_MAX_SHMEM_RATIO: Final = Decimal(1.0)
<<<<<<< HEAD
SHMEM_RATIO_KEY: Final = "resources/mem-shmem-ratio"
>>>>>>> 6dd7f0242 (rename and relocate constants and variables)
=======
SHMEM_RATIO_KEY: Final = "resources/shmem-mem-ratio"
>>>>>>> 891e0f4ab (update error message since ratio is changable)
