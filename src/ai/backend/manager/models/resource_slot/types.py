from __future__ import annotations

from pydantic import ConfigDict

from ai.backend.common.types import BackendAISchema

__all__ = ("NumberFormat",)


class NumberFormat(BackendAISchema):
    """Display number format configuration for a resource slot type."""

    model_config = ConfigDict(frozen=True)

    binary: bool = False
    round_length: int = 0
