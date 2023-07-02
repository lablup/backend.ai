import logging
import tempfile
from pathlib import Path
from typing import List

from .. import BaseRunner
from ..base import promote_path

log = logging.getLogger()

DEFAULT_BFLAGS: List[str] = [""]


class Runner(BaseRunner):
    log_prefix = "go-kernel"
    default_runtime_path = "/usr/local/bin/go"
    default_child_env = {
        **BaseRunner.default_child_env,
        "GOPATH": "/home/work",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        path_env = self.child_env["PATH"]
        path_env = promote_path(path_env, "/go/bin")
        path_env = promote_path(path_env, "/usr/local/go/bin")
        path_env = promote_path(path_env, "/home/work/bin")
        self.child_env["PATH"] = path_env

    async def init_with_loop(self):
        pass

    async def build_heuristic(self) -> int:
        if Path("main.go").is_file():
            go_glob = Path(".").glob("**/*.go")
            cmd = [
                str(self.runtime_path),
                "build",
                "-o",
                "main",
                *DEFAULT_BFLAGS,
                *map(str, go_glob),
            ]
            return await self.run_subproc(cmd)
        else:
            log.error('cannot find main file ("main.go").')
            return 127

    async def execute_heuristic(self) -> int:
        if Path("./main").is_file():
            return await self.run_subproc("./main")
        else:
            log.error('cannot find executable ("main").')
            return 127

    async def query(self, code_text) -> int:
        with tempfile.NamedTemporaryFile(suffix=".go", dir=".") as tmpf:
            tmpf.write(code_text.encode("utf8"))
            tmpf.flush()
            cmd = [str(self.runtime_path), "run", tmpf.name]
            return await self.run_subproc(cmd)

    async def complete(self, data):
        return []

    async def interrupt(self):
        # subproc interrupt is already handled by BaseRunner
        pass

    async def start_service(self, service_info):
        return None, {}
