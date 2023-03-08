import logging
import shlex
import tempfile
from pathlib import Path

from .. import BaseRunner
from ..base import glob_path, promote_path

log = logging.getLogger()


class Runner(BaseRunner):
    log_prefix = "haskell-kernel"
    default_runtime_path = "/usr/bin/ghc"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        path_env = self.child_env["PATH"]
        path_env = promote_path(path_env, glob_path("/opt/happy", "*/bin"))
        path_env = promote_path(path_env, glob_path("/opt/alex", "*/bin"))
        path_env = promote_path(path_env, glob_path("/opt/cabal", "*/bin"))
        path_env = promote_path(path_env, glob_path("/opt/ghc", "*/bin"))
        path_env = promote_path(path_env, "/home/work/.cabal/bin")
        self.child_env["PATH"] = path_env

    async def init_with_loop(self):
        pass

    async def build_heuristic(self) -> int:
        # GHC will generate error if no Main module exist among srcfiles.
        src_glob = Path(".").glob("**/*.hs")
        src_files = " ".join(map(lambda p: shlex.quote(str(p)), src_glob))
        cmd = f"ghc --make main {src_files}"
        return await self.run_subproc(cmd)

    async def execute_heuristic(self) -> int:
        if Path("./main").is_file():
            return await self.run_subproc("./main")
        else:
            log.error('cannot find executable ("main").')
            return 127

    async def query(self, code_text) -> int:
        with tempfile.NamedTemporaryFile(suffix=".hs", dir=".") as tmpf:
            tmpf.write(code_text.encode("utf8"))
            tmpf.flush()
            cmd = f"runhaskell {tmpf.name}"
            return await self.run_subproc(cmd)

    async def complete(self, data):
        return []

    async def interrupt(self):
        # subproc interrupt is already handled by BaseRunner
        pass

    async def start_service(self, service_info):
        return None, {}
