from __future__ import annotations

from dataclasses import dataclass


@dataclass
class NetAppClientArgs:
    ontap_endpoint: str
    ontap_user: str
    ontap_password: str
    verify_ssl: bool
    timeout: float


@dataclass(frozen=True)
class NetAppCluster:
    cluster_name: str
    cluster_uuid: str
    version: str
