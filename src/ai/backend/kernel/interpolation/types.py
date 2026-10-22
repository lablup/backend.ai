import enum
from typing import NotRequired, TypedDict


class InterpolationMode(enum.StrEnum):
    LEGACY = "legacy"
    DELIMITER = "delimiter"


class InterpolationDelimiterOption(TypedDict):
    start: str
    end: str


class InterpolationOption(TypedDict):
    """The ``interpolation`` entry of a service start's options."""

    # A raw ``InterpolationMode`` value; ``ServiceParser`` converts it with ``InterpolationMode(...)``.
    mode: str
    delimiter: NotRequired[InterpolationDelimiterOption | None]
