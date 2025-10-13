from abc import ABC
from typing import Self

from pydantic import BaseModel, ConfigDict, ValidationInfo

from ai.backend.logging.types import LogLevel


class BaseConfigValidationContext(BaseModel, ABC):
    debug: bool
    log_level: LogLevel

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    @classmethod
    def get_config_validation_context(cls, info: ValidationInfo) -> Self | None:
        context = info.context
        if context is None:
            return None
        if not isinstance(context, cls):
            raise ValueError(
                "context must be provided as some subtype of BaseConfigValidationContext"
            )
        return context
