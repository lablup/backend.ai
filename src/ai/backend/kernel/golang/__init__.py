import logging
import os
from pathlib import Path
import tempfile
from typing import List

from .. import BaseRunner

log = logging.getLogger()

DEFAULT_BFLAGS: List[str] = ['']


class Runner(BaseRunner):

    log_prefix = 'go-kernel'
    default_runtime_path = '/usr/local/bin/go'
    default_child_env = {
        'TERM': 'xterm',
        'LANG': 'C.UTF-8',
        'SHELL': '/bin/ash',
        'USER': 'work',
        'HOME': '/home/work',
        'PATH': '/home/work/bin:/go/bin:/usr/local/go/bin:' +
                '/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin',
        'GOPATH': '/home/work',
        'LD_LIBRARY_PATH': os.environ.get('LD_LIBRARY_PATH', ''),
        'LD_PRELOAD': os.environ.get('LD_PRELOAD', ''),
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def init_with_loop(self):
        pass

    async def build_heuristic(self) -> int:
        if Path('main.go').is_file():
            go_glob = Path('.').glob('**/*.go')
            cmd = [
                str(self.runtime_path),
                'build', '-o', 'main',
                *DEFAULT_BFLAGS, *map(str, go_glob),
            ]
            return await self.run_subproc(cmd)
        else:
            log.error('cannot find main file ("main.go").')
            return 127

    async def execute_heuristic(self) -> int:
        if Path('./main').is_file():
            return await self.run_subproc('./main')
        else:
            log.error('cannot find executable ("main").')
            return 127

    async def query(self, code_text) -> int:
        with tempfile.NamedTemporaryFile(suffix='.go', dir='.') as tmpf:
            tmpf.write(code_text.encode('utf8'))
            tmpf.flush()
            cmd = [str(self.runtime_path), 'run', tmpf.name]
            return await self.run_subproc(cmd)

    async def complete(self, data):
        return []

    async def interrupt(self):
        # subproc interrupt is already handled by BaseRunner
        pass

    async def start_service(self, service_info):
        return None, {}
