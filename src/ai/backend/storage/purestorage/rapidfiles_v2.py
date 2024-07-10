import os
from pathlib import Path
from subprocess import CalledProcessError

from ..subproc import run
from .rapidfiles import RapidFileToolsFSOpModel


class RapidFileToolsv2FSOpModel(RapidFileToolsFSOpModel):
    async def copy_tree(
        self,
        src_path: Path,
        dst_path: Path,
    ) -> None:
        extra_opts: list[bytes] = []
        if src_path.is_dir():
            extra_opts.append(b"-r")
        if dst_path.is_dir():
            extra_opts.append(b"-T")
        try:
            await run([  # noqa: F821
                b"pcopy",
                *extra_opts,
                b"-p",
                # os.fsencode(src_path / "."),  # TODO: check if "/." is necessary?
                os.fsencode(src_path),
                os.fsencode(dst_path),
            ])
        except CalledProcessError as e:
            raise RuntimeError(f'"pcopy" command failed: {e.stderr}')
