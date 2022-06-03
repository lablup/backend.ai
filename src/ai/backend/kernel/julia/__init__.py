import logging
import os
from pathlib import Path
import tempfile

import janus

from .. import BaseRunner

log = logging.getLogger()


class Runner(BaseRunner):

    log_prefix = 'julia-kernel'
    default_runtime_path = '/usr/local/julia'
    default_child_env = {
        'TERM': 'xterm',
        'LANG': 'C.UTF-8',
        'SHELL': '/bin/ash' if Path('/bin/ash').is_file() else '/bin/bash',
        'USER': 'work',
        'HOME': '/home/work',
        'PATH': ('/usr/local/julia:/usr/local/julia/bin:/usr/local/sbin:'
             '/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin'),
        'LD_LIBRARY_PATH': os.environ.get('LD_LIBRARY_PATH', ''),
        'JULIA_LOAD_PATH': ':/opt/julia',
    }
    jupyter_kspec_name = 'julia'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.input_queue = None
        self.output_queue = None

    async def init_with_loop(self):
        self.input_queue = janus.Queue()
        self.output_queue = janus.Queue()

        # We have interactive input functionality!
        self._user_input_queue = janus.Queue()
        self.user_input_queue = self._user_input_queue.async_q

        # Preparation to initialize ijulia kernel.
        cmd = '/usr/local/bin/movecompiled.sh'
        await self.run_subproc(cmd)

    async def build_heuristic(self) -> int:
        log.info('no build process for julia language')
        return 0

    async def execute_heuristic(self) -> int:
        if Path('main.jl').is_file():
            cmd = 'julia main.jl'
            return await self.run_subproc(cmd)
        else:
            log.error('cannot find executable ("main.jl").')
            return 127

    async def start_service(self, service_info):
        if service_info['name'] == 'jupyter' or service_info['name'] == 'jupyterlab':
            with tempfile.NamedTemporaryFile(
                    'w', encoding='utf-8', suffix='.py', delete=False) as config:
                print('c.NotebookApp.allow_root = True', file=config)
                print('c.NotebookApp.ip = "0.0.0.0"', file=config)
                print('c.NotebookApp.port = {}'.format(service_info['port']), file=config)
                print('c.NotebookApp.token = ""', file=config)
                print('c.FileContentsManager.delete_to_trash = False', file=config)
            jupyter_service_type = service_info['name']
            if jupyter_service_type == 'jupyter':
                jupyter_service_type = 'notebook'
            return [
                self.runtime_path, '-m', 'jupyter', jupyter_service_type,
                '--no-browser',
                '--config', config.name,
            ], {}
