import asyncio
import logging
import os
from pathlib import Path
import tempfile

from .. import BaseRunner

log = logging.getLogger()

DEFAULT_CFLAGS = ['-Wall']
DEFAULT_LDFLAGS = ['-lrt', '-lm', '-lpthread', '-ldl']


class Runner(BaseRunner):

    log_prefix = 'c-kernel'
    default_runtime_path = '/usr/bin/g++'
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
        self.user_input_queue = asyncio.Queue()

    async def clean_heuristic(self) -> int:
        if Path('Makefile').is_file():
            return await self.run_subproc('make clean')
        log.warning('skipping the clean phase due to missing "Makefile".')
        return 0

    async def build_heuristic(self) -> int:
        if self.runtime_path is None:
            raise RuntimeError('Missing runtime path')
        if Path('main.c').is_file():
            cfiles_glob = list(Path('.').glob('**/*.c'))
            ofiles_glob = [Path(p.stem + '.o') for p in sorted(cfiles_glob)]
            for cf in cfiles_glob:
                cmd = [str(self.runtime_path), '-c', str(cf), *DEFAULT_CFLAGS]
                ret = await self.run_subproc(cmd)
                if ret != 0:  # stop if gcc has failed
                    return ret
            cmd = [str(self.runtime_path), *map(str, ofiles_glob),
                   *DEFAULT_CFLAGS, '-o', './main']
            return await self.run_subproc(cmd)
        else:
            log.error('cannot find build script ("Makefile") '
                      'or the main file ("main.c").')
            return 127

    async def execute_heuristic(self) -> int:
        if Path('./main').is_file():
            return await self.run_subproc('./main')
        elif Path('./a.out').is_file():
            return await self.run_subproc('./a.out')
        else:
            log.error('cannot find executable ("a.out" or "main").')
            return 127

    async def query(self, code_text) -> int:
        with tempfile.NamedTemporaryFile(suffix='.c', dir='.') as tmpf:
            tmpf.write(code_text.encode('utf8'))
            tmpf.flush()
            cmd = [str(self.runtime_path), tmpf.name,
                   *DEFAULT_CFLAGS, '-o', './main', *DEFAULT_LDFLAGS]
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
