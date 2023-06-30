"""
This is a special kernel runner for application-only containers
which do not provide query/batch-mode code execution.
"""

import logging
from typing import List

from .. import BaseRunner

log = logging.getLogger()

DEFAULT_PYFLAGS: List[str] = []


class Runner(BaseRunner):
    log_prefix = "app-kernel"
    default_runtime_path = "/opt/backend.ai/bin/python"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def init_with_loop(self):
        pass

    async def build_heuristic(self) -> int:
        log.warning("batch-mode execution is not supported")
        return 0

    async def execute_heuristic(self) -> int:
        log.warning("batch-mode execution is not supported")
        return 0

    async def start_service(self, service_info):
        # app kernels use service-definition templates.
        return None, {}
