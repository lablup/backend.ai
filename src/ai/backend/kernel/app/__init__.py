"""
This is a special kernel runner for application-only containers
which do not provide query/batch-mode code execution.
"""

import logging
import os
from typing import List

from .. import BaseRunner

log = logging.getLogger()

DEFAULT_PYFLAGS: List[str] = []


class Runner(BaseRunner):

    log_prefix = 'app-kernel'
    default_runtime_path = '/opt/backend.ai/bin/python'
    default_child_env = {
        'TERM': 'xterm',
        'LANG': 'C.UTF-8',
        'SHELL': '/bin/bash',
        'USER': 'work',
        'HOME': '/home/work',
        'PATH': ':'.join([
            '/usr/local/nvidia/bin',
            '/usr/local/cuda/bin',
            '/usr/local/sbin',
            '/usr/local/bin',
            '/usr/sbin',
            '/usr/bin',
            '/sbin',
            '/bin',
        ]),
        'LD_LIBRARY_PATH': os.environ.get('LD_LIBRARY_PATH', ''),
        'LD_PRELOAD': os.environ.get('LD_PRELOAD', ''),
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def init_with_loop(self):
        pass

    async def build_heuristic(self) -> int:
        log.warning('batch-mode execution is not supported')
        return 0

    async def execute_heuristic(self) -> int:
        log.warning('batch-mode execution is not supported')
        return 0

    async def start_service(self, service_info):
        # app kernels use service-definition templates.
        return None, {}
