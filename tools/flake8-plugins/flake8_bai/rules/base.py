import ast
from abc import ABC, abstractmethod
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from pathlib import PurePath

from flake8_bai.codes import BAICode


@dataclass(frozen=True)
class Violation:
    line: int
    col: int
    code: BAICode


class SourcePath:
    """The checked file's path, matched by its position under the repository root, and its lines."""

    _parts: tuple[str, ...]
    _lines: tuple[str, ...]

    def __init__(self, filename: str, lines: Sequence[str]) -> None:
        self._parts = PurePath(filename).parts
        self._lines = tuple(lines)

    @property
    def name(self) -> str:
        return self._parts[-1] if self._parts else ""

    def is_under(self, directory: str) -> bool:
        """Whether the file lies under `directory` (`src/ai/backend/manager`)."""
        prefix = tuple(directory.split("/"))
        width = len(prefix)
        return any(self._parts[i : i + width] == prefix for i in range(len(self._parts) - width))

    def contains(self, text: str) -> bool:
        """Whether a line of the file contains `text`."""
        return any(text in line for line in self._lines)


class Rule(ABC):
    @abstractmethod
    def applies_to(self, path: SourcePath) -> bool:
        raise NotImplementedError

    @abstractmethod
    def check(self, tree: ast.Module) -> Iterator[Violation]:
        raise NotImplementedError
