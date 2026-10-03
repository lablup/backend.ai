from __future__ import annotations

import tomllib
from importlib.resources.abc import Traversable
from typing import Any

import orjson
import yaml

from ai.backend.common.json import load_json
from ai.backend.common.serde.exceptions import InvalidFileContent
from ai.backend.common.serde.types import FileFormat

__all__ = ("FileLoader",)


class FileLoader:
    """Loads a file into plain Python values in the format its suffix names. A YAML file
    is read as one document."""

    def load(self, entry: Traversable) -> Any:
        return self.parse(entry.name, entry.read_text(encoding="utf-8"))

    def parse(self, name: str, text: str) -> Any:
        file_format = FileFormat.from_name(name)
        try:
            match file_format:
                case FileFormat.YAML:
                    return yaml.safe_load(text)
                case FileFormat.JSON:
                    return load_json(text)
                case FileFormat.TOML:
                    return tomllib.loads(text)
        except (yaml.YAMLError, orjson.JSONDecodeError, tomllib.TOMLDecodeError) as e:
            raise InvalidFileContent(f"{name} is not readable as {file_format}: {e}") from e
