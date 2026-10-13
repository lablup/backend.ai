from __future__ import annotations

from dataclasses import dataclass


@dataclass
class DellEMCOneFSClientArgs:
    endpoint: str
    username: str
    password: str
    api_version: str
    verify_ssl: bool
    timeout: float


@dataclass(frozen=True)
class OneFSCluster:
    cluster_name: str
    release: str
    build: str
