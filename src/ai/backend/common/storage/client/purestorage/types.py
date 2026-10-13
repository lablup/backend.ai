from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PureStorageClientArgs:
    endpoint: str
    api_token: str
    api_version: str
    verify_ssl: bool
    timeout: float


@dataclass(frozen=True)
class PureStorageArray:
    array_id: str
    array_name: str
    os: str
    version: str
