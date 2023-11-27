import logging
import tempfile
from pathlib import Path

from .. import BaseRunner

log = logging.getLogger()


class Runner(BaseRunner):
    log_prefix = "nodejs-kernel"
    default_runtime_path = "/usr/bin/local/node"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def init_with_loop(self):
        pass

    async def build_heuristic(self) -> int:
        log.info("no build process for node.js language")
        return 0

    async def execute_heuristic(self) -> int:
        if Path("main.js").is_file():
            cmd = [str(self.runtime_path), "main.js"]
            return await self.run_subproc(cmd)
        else:
            log.error('cannot find executable ("main.js").')
            return 127

    async def query(self, code_text) -> int:
        with tempfile.NamedTemporaryFile(suffix=".js", dir=".") as tmpf:
            tmpf.write(code_text.encode("utf8"))
            tmpf.flush()
            cmd = [str(self.runtime_path), tmpf.name]
            return await self.run_subproc(cmd)

    async def complete(self, data):
        return []

    async def interrupt(self):
        # subproc interrupt is already handled by BaseRunner
        pass

    async def start_service(self, service_info):
        print(service_info["name"])
        if service_info["name"] == "node":
            return [
                self.runtime_path,
                "-m",
                "node",
            ], {}
