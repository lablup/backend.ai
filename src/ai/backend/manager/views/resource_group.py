from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ResourceGroupProxyTargetWithOptionalToken:
    addr: str
    api_token: str | None
