from __future__ import annotations

from dataclasses import dataclass


@dataclass
class GPFSClientArgs:
    endpoint: str
    username: str
    password: str
    verify_ssl: bool
    timeout: float


@dataclass(frozen=True)
class GPFSCluster:
    cluster_name: str
    cluster_id: str
