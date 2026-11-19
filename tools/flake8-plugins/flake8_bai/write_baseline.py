"""Print the baseline of the current violations, leaving out the `per-file-ignores` of `.flake8`.

From the repository root: `PYTHONPATH=tools/flake8-plugins python -m flake8_bai.write_baseline src > tools/flake8-plugins/flake8_bai/baseline.txt`
"""

import ast
import configparser
import sys
from pathlib import Path

from flake8_bai.plugin import Plugin


class BaselineWriter:
    _per_file_ignores: dict[str, frozenset[str]]

    def __init__(self, config_path: Path) -> None:
        parser = configparser.ConfigParser()
        parser.read(config_path)
        self._per_file_ignores = {}
        for line in parser.get("flake8", "per-file-ignores", fallback="").splitlines():
            if ":" not in line:
                continue
            filename, codes = line.split(":", 1)
            self._per_file_ignores[filename.strip()] = frozenset(
                code.strip() for code in codes.split(",")
            )

    def write(self, roots: list[str]) -> None:
        sys.stdout.write(
            "# Violations in main when their rule was added. Fix a file and drop its line.\n"
        )
        sys.stdout.write("# Regenerate: see the docstring of flake8_bai/write_baseline.py\n")
        for root in roots:
            for path in sorted(Path(root).rglob("*.py")):
                codes = self._codes(path)
                if codes:
                    sys.stdout.write(f"{path.as_posix()}: {','.join(sorted(codes))}\n")

    def _codes(self, path: Path) -> set[str]:
        tree = ast.parse(path.read_text(), filename=str(path))
        allowed = self._per_file_ignores.get(path.as_posix(), frozenset())
        return {
            violation.code.code
            for violation in Plugin(tree, path.as_posix()).violations()
            if violation.code.code not in allowed
        }


if __name__ == "__main__":
    BaselineWriter(Path(".flake8")).write(sys.argv[1:])
