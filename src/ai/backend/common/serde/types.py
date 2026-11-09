from __future__ import annotations

import enum
from pathlib import PurePath
from typing import Self

from ai.backend.common.serde.exceptions import UnsupportedFileFormat

__all__ = ("FileFormat",)


class FileFormat(enum.StrEnum):
    """The formats a file is read in, chosen by the suffix of its name."""

    YAML = "yaml"
    JSON = "json"
    TOML = "toml"

    @classmethod
    def from_name(cls, name: str) -> Self:
        suffix = PurePath(name).suffix.lower()
        for file_format in cls:
            if suffix in file_format.suffixes():
                return file_format
        raise UnsupportedFileFormat(
            f"{name}: {suffix or 'no suffix'} is not one of {sorted(cls.all_suffixes())}"
        )

    @classmethod
    def all_suffixes(cls) -> frozenset[str]:
        return frozenset(suffix for file_format in cls for suffix in file_format.suffixes())

    def suffixes(self) -> frozenset[str]:
        match self:
            case FileFormat.YAML:
                return frozenset({".yaml", ".yml"})
            case FileFormat.JSON:
                return frozenset({".json"})
            case FileFormat.TOML:
                return frozenset({".toml"})
