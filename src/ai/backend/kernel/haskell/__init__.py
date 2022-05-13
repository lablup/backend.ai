import logging
import os
from pathlib import Path
import shlex
import tempfile

from .. import BaseRunner

log = logging.getLogger()


class Runner(BaseRunner):

    log_prefix = 'haskell-kernel'
    default_runtime_path = '/usr/bin/ghc'
    default_child_env = {
        'TERM': 'xterm',
        'LANG': 'C.UTF-8',
        'SHELL': '/bin/bash',
        'USER': 'work',
        'HOME': '/home/work',
        'PATH': ('/root/.cabal/bin:/root/.local/bin:/opt/cabal/2.0/bin:'
                 '/opt/ghc/8.2.1/bin:/opt/happy/1.19.5/bin:/opt/alex/3.1.7/bin:'
                 '/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin'),
        'LD_LIBRARY_PATH': os.environ.get('LD_LIBRARY_PATH', ''),
        'LD_PRELOAD': os.environ.get('LD_PRELOAD', ''),
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def init_with_loop(self):
        pass

    async def build_heuristic(self) -> int:
        # GHC will generate error if no Main module exist among srcfiles.
        src_glob = Path('.').glob('**/*.hs')
        src_files = ' '.join(map(lambda p: shlex.quote(str(p)), src_glob))
        cmd = f'ghc --make main {src_files}'
        return await self.run_subproc(cmd)

    async def execute_heuristic(self) -> int:
        if Path('./main').is_file():
            return await self.run_subproc('./main')
        else:
            log.error('cannot find executable ("main").')
            return 127

    async def query(self, code_text) -> int:
        with tempfile.NamedTemporaryFile(suffix='.hs', dir='.') as tmpf:
            tmpf.write(code_text.encode('utf8'))
            tmpf.flush()
            cmd = f'runhaskell {tmpf.name}'
            return await self.run_subproc(cmd)

    async def complete(self, data):
        return []

    async def interrupt(self):
        # subproc interrupt is already handled by BaseRunner
        pass

    async def start_service(self, service_info):
        return None, {}
