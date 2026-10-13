from __future__ import annotations

from dataclasses import dataclass


@dataclass
class VASTClientArgs:
    endpoint: str
    username: str
    password: str
    api_version: str
    cluster_id: int
    verify_ssl: bool
    timeout: float


@dataclass(frozen=True)
class VASTCluster:
    cluster_name: str
    state: str
    guid: str
