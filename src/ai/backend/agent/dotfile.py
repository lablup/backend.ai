from itertools import takewhile
from pathlib import Path

from ai.backend.common.dotfile import DotfilePath, InvalidDotfilePath


class DotfileTargetResolver:
    """Maps dotfile paths to host paths inside a kernel's work directory."""

    _work_dir: Path

    def __init__(self, work_dir: Path) -> None:
        self._work_dir = work_dir.resolve()

    def resolve(self, raw_path: str) -> Path:
        """Symlinks already in the work directory are followed before the containment check."""
        target = (self._work_dir / DotfilePath(raw_path).relative).resolve()
        if target == self._work_dir or not target.is_relative_to(self._work_dir):
            raise InvalidDotfilePath("dotfile path must stay under the kernel work directory.")
        return target

    def paths_below_work_dir(self, target: Path) -> list[Path]:
        """The target and its parents, excluding the work directory."""
        return [target, *takewhile(lambda path: path != self._work_dir, target.parents)]
