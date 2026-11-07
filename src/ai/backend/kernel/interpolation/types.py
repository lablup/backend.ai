from collections.abc import Sequence
from typing import TypedDict


class InterpolationDelimiter(TypedDict):
    start: str
    end: str


class InterpolationOption(TypedDict):
    """The ``interpolation`` entry of a service start's options."""

    delimiters: Sequence[InterpolationDelimiter]
