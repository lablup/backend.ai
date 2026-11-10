from __future__ import annotations

from ai.backend.common.types import BackendAISchema


class LustreServerConnection(BackendAISchema):
    name: str
    state: str


class LustreProjectQuota(BackendAISchema):
    used_bytes: int
    limit_bytes: int
