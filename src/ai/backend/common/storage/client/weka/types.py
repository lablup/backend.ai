from __future__ import annotations

from dataclasses import dataclass


@dataclass
class WekaClientArgs:
    endpoint: str
    username: str
    password: str
    organization: str
    verify_ssl: bool
    timeout: float


@dataclass(frozen=True)
class WekaCluster:
    cluster_name: str
    status: str
    release: str
