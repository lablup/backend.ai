from __future__ import annotations

import time

from pydantic import Field

from ai.backend.common.types import BackendAISchema


class WekaLoginRequest(BackendAISchema):
    username: str
    password: str
    org: str


class WekaRefreshLoginRequest(BackendAISchema):
    refresh_token: str


class WekaSetQuotaRequest(BackendAISchema):
    grace_seconds: int | None = None
    soft_limit_bytes: str
    hard_limit_bytes: str


class WekaSetQuotaV1Params(BackendAISchema):
    activate: bool = True
    inode_context: int
    path: str
    soft_limit_bytes: int | None = None
    hard_limit_bytes: int | None = None


class WekaSetQuotaV1Request(BackendAISchema):
    """JSON-RPC body of the V1 ``set_directory_quota`` call."""

    id: float = Field(default_factory=lambda: time.time() * 1000)
    jsonrpc: str = "2.0"
    method: str = "set_directory_quota"
    params: WekaSetQuotaV1Params


class WekaGetMetricQuery(BackendAISchema):
    start_time: str
    end_time: str | None = None
    category: str | None = None
    stat: list[str]
