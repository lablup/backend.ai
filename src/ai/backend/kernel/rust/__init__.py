import logging
import os
from pathlib import Path
import tempfile

from .. import BaseRunner
from ..utils import find_executable

log = logging.getLogger()

CARGO = 'cargo'
RUSTC = 'rustc'


class Runner(BaseRunner):

    log_prefix = 'rust-kernel'
    default_runtime_path = '/usr/bin/rustc'
    default_child_env = {
        'TERM': 'xterm',
        'LANG': 'C.UTF-8',
        'SHELL': '/bin/ash',
        'USER': 'work',
        'HOME': '/home/work',
        'PATH': '/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin',
        'GOPATH': '/home/work',
        'LD_LIBRARY_PATH': os.environ.get('LD_LIBRARY_PATH', ''),
        'LD_PRELOAD': os.environ.get('LD_PRELOAD', ''),
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def init_with_loop(self):
        pass

    async def build_heuristic(self) -> int:
        if Path('Cargo.toml').is_file():
            return await self.run_subproc([CARGO, 'build'])
        elif Path('main.rs').is_file():
            return await self.run_subproc([RUSTC, '-o', 'main', 'main.rs'])
        else:
            log.error(
                'cannot find the main/build file ("Cargo.toml" or "main.rs").')
            return 127

    async def execute_heuristic(self) -> int:
        out = find_executable('./target/debug', './target/release')
        if out is not None:
            return await self.run_subproc([out])
        elif Path('./main').is_file():
            return await self.run_subproc(['./main'])
        else:
            log.error('cannot find executable ("main" or target directories).')
            return 127

    async def query(self, code_text) -> int:
        with tempfile.NamedTemporaryFile(suffix='.rs', dir='.') as tmpf:
            tmpf.write(code_text.encode('utf8'))
            tmpf.flush()
            cmd = [RUSTC, '-o', 'main', tmpf.name]
            ret = await self.run_subproc(cmd)
            if ret != 0:
                return ret
            cmd = ['./main']
            return await self.run_subproc(cmd)

    async def complete(self, data):
        return []

    async def interrupt(self):
        # subproc interrupt is already handled by BaseRunner
        pass

    async def start_service(self, service_info):
        return None, {}
