from itertools import takewhile
from pathlib import Path

from ai.backend.common.dotfile import DotfilePath, InvalidDotfilePath


class DotfileTargetResolver:
    """Maps dotfile paths to host paths inside a kernel's work directory."""

    _work_dir: Path

    def __init__(self, work_dir: Path) -> None:
        self._work_dir = work_dir.resolve()

    def resolve(self, raw_path: str) -> Path:
        """Rejects a path with a symlink at any step, inside or outside the work directory."""
        target = self._work_dir
        for segment in DotfilePath(raw_path).relative.parts:
            target /= segment
            if target.is_symlink():
                raise InvalidDotfilePath("dotfile path must not pass through a symbolic link.")
        return target

    def paths_below_work_dir(self, target: Path) -> list[Path]:
        """The target and its parents, excluding the work directory."""
        return [target, *takewhile(lambda path: path != self._work_dir, target.parents)]
