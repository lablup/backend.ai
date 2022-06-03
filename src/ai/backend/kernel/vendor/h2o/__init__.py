import asyncio
import logging
import os
from pathlib import Path
import tempfile
from typing import List

from ... import BaseRunner

log = logging.getLogger()

DEFAULT_PYFLAGS: List[str] = []


class Runner(BaseRunner):

    log_prefix = 'h2o-kernel'
    default_runtime_path = '/opt/h2oai/dai/python/bin/python'
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
        self.user_input_queue = asyncio.Queue()

        # Load H2O Daemon.
        print('Daemonizing H2O (run-dai.sh)...')
        Path('/opt/h2oai/dai').mkdir(parents=True, exist_ok=True)
        cmd = ['/opt/h2oai/dai/run-dai.sh']
        await self.run_subproc(cmd)

    async def build_heuristic(self) -> int:
        if Path('setup.py').is_file():
            cmd = [
                str(self.runtime_path), *DEFAULT_PYFLAGS,
                '-m', 'pip', 'install', '--user', '-e', '.',
            ]
            return await self.run_subproc(cmd)
        else:
            log.warning('skipping the build phase due to missing "setup.py" file')
            return 0

    async def execute_heuristic(self) -> int:
        if Path('main.py').is_file():
            cmd = [
                str(self.runtime_path), *DEFAULT_PYFLAGS,
                'main.py',
            ]
            return await self.run_subproc(cmd)
        else:
            log.error('cannot find the main script ("main.py").')
            return 127

    async def start_service(self, service_info):
        if service_info['name'] in ['jupyter', 'jupyterlab']:
            with tempfile.NamedTemporaryFile(
                    'w', encoding='utf-8', suffix='.py', delete=False) as config:
                print('c.NotebookApp.allow_root = True', file=config)
                print('c.NotebookApp.ip = "0.0.0.0"', file=config)
                print('c.NotebookApp.port = {}'.format(service_info['port']), file=config)
                print('c.NotebookApp.token = ""', file=config)
                print('c.FileContentsManager.delete_to_trash = False', file=config)
                print('c.NotebookApp.tornado_settings = {\'ws_ping_interval\': 10000}', file=config)
            jupyter_service_type = service_info['name']
            if jupyter_service_type == 'jupyter':
                jupyter_service_type = 'notebook'
            return [
                self.runtime_path, '-m', jupyter_service_type,
                '--no-browser',
                '--config', config.name,
            ], {}
        elif 'h2o' in service_info['name']:
            return ['echo', 'h2o daemon already started'], {}
        elif service_info['name'] == 'sftp':
            return [
                self.runtime_path,
                '-m', 'sftpserver',
                '--port', str(service_info['port']),
            ], {}
