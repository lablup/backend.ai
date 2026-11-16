import asyncio
import logging

from ai.backend.accelerator.rebellions.common.atom_api import ATOMAPI, ATOMStat, LibraryError
from ai.backend.logging.structured import StructuredLogger

log = StructuredLogger(logging.getLogger(__spec__.name))


class Rebel100API(ATOMAPI):
    @classmethod
    async def get_stats(cls, exec_path: str) -> ATOMStat:
        # A non-zero exit fails; stderr alone is logged, so tool warnings do not disable the plugin.
        proc = await asyncio.create_subprocess_exec(
            exec_path,
            "-g",
            "-j",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        out, err = await proc.communicate()
        if proc.returncode:
            raise LibraryError(
                f"Error while executing rbln-smi -g -j (exit code {proc.returncode}):"
                f" {err.decode('utf-8')}"
            )
        if err:
            log.debug("rbln-smi wrote to stderr", stderr=err.decode("utf-8", errors="replace"))
        return ATOMStat.from_json(out.decode("utf-8"))
