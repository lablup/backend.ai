from __future__ import annotations

from ai.backend.common.api_handlers import BaseResponseModel


class StreamAppItem(BaseResponseModel):
    """A single application service port entry."""

    name: str
    protocol: str
    ports: list[int]
    url_template: str | None = None
    allowed_arguments: list[str] | None = None
    allowed_envs: list[str] | None = None
