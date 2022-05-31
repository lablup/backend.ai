import logging
import os
import tempfile

from .. import BaseRunner

log = logging.getLogger()


class Runner(BaseRunner):

    log_prefix = 'scheme-kernel'
    default_runtime_path = '/usr/bin/rustc'
    default_child_env = {
        'TERM': 'xterm',
        'LANG': 'C.UTF-8',
        'SHELL': '/bin/ash',
        'USER': 'work',
        'HOME': '/home/work',
        'PATH': '/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin',
        'LD_LIBRARY_PATH': os.environ.get('LD_LIBRARY_PATH', ''),
        'LD_PRELOAD': os.environ.get('LD_PRELOAD', ''),
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def init_with_loop(self):
        pass

    async def build_heuristic(self) -> int:
        pass

    async def execute_heuristic(self) -> int:
        pass

    async def query(self, code_text) -> int:
        with tempfile.NamedTemporaryFile(suffix='.scm', dir='.') as tmpf:
            tmpf.write(code_text.encode('utf8'))
            tmpf.flush()
            cmd = f'scheme --quiet < {tmpf.name}'
            return await self.run_subproc(cmd)

    async def complete(self, data):
        return []

    async def interrupt(self):
        # subproc interrupt is already handled by BaseRunner
        pass

    async def start_service(self, service_info):
        return None, {}
