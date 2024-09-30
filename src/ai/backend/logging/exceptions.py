from __future__ import annotations

from typing import Any, Mapping


class ConfigurationError(Exception):
    invalid_data: Mapping[str, Any]

    def __init__(self, invalid_data: Mapping[str, Any]) -> None:
        super().__init__(invalid_data)
        self.invalid_data = invalid_data
