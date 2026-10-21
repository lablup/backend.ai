import enum
from typing import NotRequired, TypedDict


class InterpolationMode(enum.StrEnum):
    """Mirrors ``ai.backend.common.config.ServiceInterpolationMode``."""

    LEGACY = "legacy"
    DELIMITER = "delimiter"


class InterpolationDelimiterOption(TypedDict):
    start: str
    end: str


class InterpolationOption(TypedDict):
    """Shape of ``ModelServiceConfig.interpolation`` once dumped."""

    # A raw ``InterpolationMode`` value; ``ServiceParser`` converts it with ``InterpolationMode(...)``.
    mode: str
    delimiter: NotRequired[InterpolationDelimiterOption | None]
