from __future__ import annotations

import functools
import os


@functools.lru_cache
def get_parallel_slot() -> int:
    return int(os.environ.get("BACKEND_TEST_EXEC_SLOT", "0"))
