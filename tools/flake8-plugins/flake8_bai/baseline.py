from importlib.resources import files
from pathlib import Path, PurePath


class Baseline:
    """Violations allowed per file: lines of `<path>: <code>,<code>`, `#` for comments."""

    _codes_by_path: dict[str, frozenset[str]]

    def __init__(self, codes_by_path: dict[str, frozenset[str]]) -> None:
        self._codes_by_path = codes_by_path

    @classmethod
    def empty(cls) -> "Baseline":
        return cls({})

    @classmethod
    def load(cls, resource: str) -> "Baseline":
        """Read `resource` from the `flake8_bai` package, where pants and `.flake8` both find it."""
        codes_by_path: dict[str, frozenset[str]] = {}
        for raw_line in files("flake8_bai").joinpath(resource).read_text().splitlines():
            line = raw_line.split("#", 1)[0].strip()
            if not line:
                continue
            filename, codes = line.split(":", 1)
            codes_by_path[filename.strip()] = frozenset(
                code.strip() for code in codes.split(",") if code.strip()
            )
        return cls(codes_by_path)

    def allows(self, filename: str, code: str) -> bool:
        return code in self._codes_by_path.get(self._normalize(filename), frozenset())

    def _normalize(self, filename: str) -> str:
        path = PurePath(filename)
        if path.is_absolute() and path.is_relative_to(Path.cwd()):
            path = path.relative_to(Path.cwd())
        return path.as_posix()
