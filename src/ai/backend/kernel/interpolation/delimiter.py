import re
from collections.abc import Mapping
from typing import Any, Self, override

from ai.backend.kernel.exception import InvalidServiceDefinition
from ai.backend.kernel.interpolation.base import AbstractServiceInterpolator
from ai.backend.kernel.interpolation.types import InterpolationOption


class DelimiterInterpolator(AbstractServiceInterpolator):
    """Only ``<start> var <end>`` is filled; every other character, braces included, stays."""

    _pattern: re.Pattern[str]

    def __init__(self, variables: Mapping[str, Any], start: str, end: str) -> None:
        super().__init__(variables)
        self._pattern = re.compile(rf"{re.escape(start)}\s*(?P<expr>.*?)\s*{re.escape(end)}")

    @override
    @classmethod
    def from_option(cls, variables: Mapping[str, Any], option: InterpolationOption) -> Self:
        delimiter = option.get("delimiter")
        if delimiter is None:
            raise InvalidServiceDefinition("delimiter interpolation requires a delimiter")
        return cls(variables, delimiter["start"], delimiter["end"])

    @property
    @override
    def pattern(self) -> re.Pattern[str]:
        return self._pattern
