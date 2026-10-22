import functools
import re
from typing import override

from ai.backend.kernel.exception import InvalidServiceDefinition
from ai.backend.kernel.interpolation.base import BaseServiceInterpolator
from ai.backend.kernel.interpolation.types import InterpolationOption


class DelimiterInterpolator(BaseServiceInterpolator):
    """Only ``<start> var <end>`` is filled; every other character, braces included, stays."""

    @override
    def pattern(self, option: InterpolationOption) -> re.Pattern[str]:
        delimiter = option.get("delimiter")
        if delimiter is None:
            raise InvalidServiceDefinition("delimiter interpolation requires a delimiter")
        return self._compile(delimiter["start"], delimiter["end"])

    @staticmethod
    @functools.cache
    def _compile(start: str, end: str) -> re.Pattern[str]:
        return re.compile(rf"{re.escape(start)}\s*(?P<expr>.*?)\s*{re.escape(end)}")
