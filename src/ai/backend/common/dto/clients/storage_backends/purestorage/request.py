from __future__ import annotations

from ai.backend.common.types import BackendAISchema


class PurityListQuery(BackendAISchema):
    names: str | None = None
    protocol: str | None = None
    items_returned: int = 10
    token: str = ""
