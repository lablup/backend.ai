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


DEFAULT_SHARED_MEMORY_SIZE: Final = "64m"
DEFAULT_ALLOWED_MAX_SHMEM_RATIO: Final = Decimal(1.0)
SHMEM_RATIO_KEY: Final = "resources/shmem-mem-ratio"
