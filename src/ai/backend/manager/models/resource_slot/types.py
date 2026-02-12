from __future__ import annotations

from pydantic import BaseModel, ConfigDict

__all__ = ("NumberFormat",)


class NumberFormat(BaseModel):
    """Display number format configuration for a resource slot type."""

    model_config = ConfigDict(frozen=True)

    binary: bool = False
    round_length: int = 0
