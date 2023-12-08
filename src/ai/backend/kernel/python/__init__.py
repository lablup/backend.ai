import asyncio
import logging
import os
import shutil
import tempfile
from pathlib import Path
from typing import List

import janus

from .. import BaseRunner
from ..base import promote_path

log = logging.getLogger()

DEFAULT_PYFLAGS: List[str] = []


class Runner(BaseRunner):
    log_prefix = "python-kernel"
    default_runtime_path = "/usr/bin/python"
    default_child_env = {
        **BaseRunner.default_child_env,
        "PYTHONPATH": os.environ.get("PYTHONPATH", ""),
    }
    jupyter_kspec_name = "python"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.input_queue = None
        self.output_queue = None

    async def init_with_loop(self):
        self.input_queue = janus.Queue()
        self.output_queue = janus.Queue()

        # We have interactive input functionality for query mode!
        self._user_input_queue = janus.Queue()
        self.user_input_queue = self._user_input_queue.async_q

        # Get USER_SITE for runtime python.
        cmd = [self.runtime_path, *DEFAULT_PYFLAGS, "-c", "import site; print(site.USER_SITE)"]
        proc = await asyncio.create_subprocess_exec(
            *map(str, cmd),
            env=self.child_env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()
        user_site = stdout.decode("utf8").strip()
        self.child_env["PYTHONPATH"] = promote_path(self.child_env["PYTHONPATH"], user_site)

        # Add support for interactive input in batch mode by copying
        # sitecustomize.py to USER_SITE of runtime python.
        sitecustomize_path = Path(os.path.dirname(__file__)) / "sitecustomize.py"
        user_site = Path(user_site)
        user_site.mkdir(parents=True, exist_ok=True)
        shutil.copy(str(sitecustomize_path), str(user_site / "sitecustomize.py"))

    async def build_heuristic(self) -> int:
        if Path("setup.py").is_file():
            cmd = [
                str(self.runtime_path),
                *DEFAULT_PYFLAGS,
                "-m",
                "pip",
                "install",
                "--user",
                "-e",
                ".",
            ]
            return await self.run_subproc(cmd)
        else:
            log.warning('skipping the build phase due to missing "setup.py" file')
            return 0

    async def execute_heuristic(self) -> int:
        if Path("main.py").is_file():
            cmd = [
                str(self.runtime_path),
                *DEFAULT_PYFLAGS,
                "main.py",
            ]
            return await self.run_subproc(cmd, batch=True)
        else:
            log.error('cannot find the main script ("main.py").')
            return 127

    async def start_service(self, service_info):
        if service_info["name"] in ["jupyter", "jupyterlab"]:
            with tempfile.NamedTemporaryFile(
                "w", encoding="utf-8", suffix=".py", delete=False
            ) as config:
                print("c.NotebookApp.allow_root = True", file=config)
                print('c.NotebookApp.ip = "0.0.0.0"', file=config)
                print("c.NotebookApp.port = {}".format(service_info["port"]), file=config)
                print('c.NotebookApp.token = ""', file=config)
                print("c.FileContentsManager.delete_to_trash = False", file=config)
                print("c.NotebookApp.tornado_settings = {'ws_ping_interval': 10000}", file=config)
            jupyter_service_type = service_info["name"]
            if jupyter_service_type == "jupyter":
                jupyter_service_type = "notebook"
            return [
                self.runtime_path,
                "-m",
                jupyter_service_type,
                "--no-browser",
                "--config",
                config.name,
            ], {}
        elif service_info["name"] == "ipython":
            return [
                self.runtime_path,
                "-m",
                "IPython",
            ], {}
        elif service_info["name"] == "digits":
            return [
                self.runtime_path,
                "-m",
                "digits",
            ], {}
        elif service_info["name"] == "tensorboard":
            Path("/home/work/logs").mkdir(parents=True, exist_ok=True)
            return [
                self.runtime_path,
                "-m",
                "tensorboard.main",
                "--logdir",
                "/home/work/logs",
                "--host",
                "0.0.0.0",
                "--port",
                str(service_info["port"]),
                "--debugger_port",
                "6064",  # used by in-container TensorFlow
            ], {}
        elif service_info["name"] == "spectravis":
            return (
                [
                    self.runtime_path,
                    "-m",
                    "http.server",
                    "8000",
                ],
                {},
                "/home/work/spectravis",
            )
        elif service_info["name"] == "sftp":
            return [
                self.runtime_path,
                "-m",
                "sftpserver",
                "--port",
                str(service_info["port"]),
            ], {}
        return None, None
