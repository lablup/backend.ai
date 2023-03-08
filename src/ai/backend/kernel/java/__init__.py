import asyncio
import logging
import os
import re
import shlex
import tempfile
from pathlib import Path

from .. import BaseRunner
from ..base import glob_path, promote_path

log = logging.getLogger()

JCC = "javac"
JCR = "java"

# Let Java respect container resource limits
DEFAULT_JFLAGS = [
    "-J-XX:+UnlockExperimentalVMOptions",
    "-J-XX:+UseCGroupMemoryLimitForHeap",
    "-d",
    ".",
]


class Runner(BaseRunner):
    log_prefix = "java-kernel"
    default_runtime_path = os.fsdecode(glob_path("/usr/lib/jvm", "java-*/bin/java") or "/usr/bin")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        path_env = self.child_env["PATH"]
        path_env = promote_path(path_env, glob_path("/usr/lib/jvm", "java-*/jre/bin"))
        path_env = promote_path(path_env, glob_path("/usr/lib/jvm", "java-*/bin"))
        self.child_env["PATH"] = path_env

    def _code_for_user_input_server(self, code: str) -> str:
        # TODO: More elegant way of not touching user code? This method does not work
        #       for batch exec (no way of knowing the main file).
        #       Way of monkey patching System.in?
        modules = "import java.io.*;"
        static_initializer = (
            r"\1static{BackendInputStream stream = "
            r"new BackendInputStream();System.setIn(stream);}"
        )
        patch = Path(os.path.dirname(__file__)) / "LablupPatches.java"
        altered = re.sub(r"(public[\s]+class[\s]+[\w]+[\s]*{)", static_initializer, code)
        altered = modules + altered
        altered = altered + "\n\n" + patch.read_text()
        return altered

    async def init_with_loop(self):
        self.user_input_queue = asyncio.Queue()

    async def build_heuristic(self) -> int:
        if Path("Main.java").is_file():
            java_sources = Path(".").glob("**/*.java")
            java_source_list = " ".join(map(lambda p: shlex.quote(str(p)), java_sources))
            cmd = [JCC, *DEFAULT_JFLAGS, java_source_list]
            return await self.run_subproc(cmd)
        else:
            java_sources = Path(".").glob("**/*.java")
            java_source_list = " ".join(map(lambda p: shlex.quote(str(p)), java_sources))
            cmd = [JCC, *DEFAULT_JFLAGS, java_source_list]
            return await self.run_subproc(cmd)

    async def execute_heuristic(self) -> int:
        if Path("./main/Main.class").is_file():
            return await self.run_subproc([JCR, "main.Main"])
        elif Path("./Main.class").is_file():
            return await self.run_subproc([JCR, "Main"])
        else:
            log.error("cannot find entry class (main.Main).")
            return 127

    async def query(self, code_text) -> int:
        # Try to get the name of the first public class using a simple regular
        # expression and use it as the name of the main source/class file.
        # (In Java, the main function must reside in a public class as a public
        # static void method where the filename must be same to the class name)
        #
        # NOTE: This approach won't perfectly handle all edge cases!
        with tempfile.TemporaryDirectory() as tmpdir:
            m = re.search(r"public[\s]+class[\s]+([\w]+)[\s]*{", code_text)
            if m:
                mainpath = Path(tmpdir) / (m.group(1) + ".java")
            else:
                # TODO: wrap the code using a class skeleton??
                mainpath = Path(tmpdir) / "main.java"
            code = self._code_for_user_input_server(code_text)
            with open(mainpath, "w", encoding="utf-8") as tmpf:
                tmpf.write(code)
            ret = await self.run_subproc([JCC, str(mainpath)])
            if ret != 0:
                return ret
            cmd = [JCR, "-classpath", tmpdir, mainpath.stem]
            return await self.run_subproc(cmd)

    async def complete(self, data):
        return []

    async def interrupt(self):
        # subproc interrupt is already handled by BaseRunner
        pass

    async def start_service(self, service_info):
        return None, {}
