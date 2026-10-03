from __future__ import annotations

import tomllib
from collections.abc import Mapping
from importlib.resources.abc import Traversable

import orjson
import yaml

from ai.backend.common.json import load_json
from ai.backend.common.serde.exceptions import InvalidFileContent
from ai.backend.common.serde.types import FileFormat

__all__ = ("FileLoader",)


class FileLoader:
    """Loads a file whose top level is a mapping, in the format its suffix names. A YAML
    file is read as one document; any other top level is refused."""

    def load(self, entry: Traversable) -> Mapping[str, object]:
        return self.parse(entry.name, entry.read_text(encoding="utf-8"))

    def parse(self, name: str, text: str) -> Mapping[str, object]:
        file_format = FileFormat.from_name(name)
        try:
            value = self._decode(file_format, text)
        except (yaml.YAMLError, orjson.JSONDecodeError, tomllib.TOMLDecodeError) as e:
            raise InvalidFileContent(f"{name} is not readable as {file_format}: {e}") from e
        if not isinstance(value, Mapping):
            raise InvalidFileContent(
                f"{name}: the top level is {type(value).__name__}, not a mapping"
            )
        return value

    def _decode(self, file_format: FileFormat, text: str) -> object:
        match file_format:
            case FileFormat.YAML:
                return yaml.safe_load(text)
            case FileFormat.JSON:
                return load_json(text)
            case FileFormat.TOML:
                return tomllib.loads(text)
