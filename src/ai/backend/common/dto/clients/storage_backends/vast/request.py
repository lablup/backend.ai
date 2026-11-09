from __future__ import annotations

from ai.backend.common.types import BackendAISchema


class VASTLoginRequest(BackendAISchema):
    username: str
    password: str


class VASTRefreshTokenRequest(BackendAISchema):
    refresh_token: str


class VASTSetQuotaRequest(BackendAISchema):
    name: str
    path: str
    create_dir: bool = False
    soft_limit: int | None = None
    hard_limit: int | None = None
    soft_limit_inodes: int | None = None
    hard_limit_inodes: int | None = None
    grace_period: str | None = None


class VASTModifyQuotaRequest(BackendAISchema):
    soft_limit: int | None = None
    hard_limit: int | None = None
    soft_limit_inodes: int | None = None
    hard_limit_inodes: int | None = None
    grace_period: str | None = None


class VASTListQuotasQuery(BackendAISchema):
    name: str | None = None
