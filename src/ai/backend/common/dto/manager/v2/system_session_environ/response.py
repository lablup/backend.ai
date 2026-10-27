"""Response DTOs for system session environ DTO v2."""

from __future__ import annotations

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel

__all__ = ("ListSystemSessionEnvironValueSourcesPayload",)


class ListSystemSessionEnvironValueSourcesPayload(BaseResponseModel):
    """Every value source a system session environ row can carry."""

    items: list[str] = Field(description="The value source names a row can carry.")
