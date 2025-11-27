from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class ScalingGroupData:
    name: str
    description: str
    is_active: bool
    is_public: bool
    created_at: datetime
    wsproxy_addr: str
    wsproxy_api_token: str
    driver: str
    driver_opts: Mapping[str, Any]
    scheduler: str
    scheduler_opts: Mapping[str, Any]
    use_host_network: bool


@dataclass
class ScalingGroupListResult:
    """Result of searching scaling groups."""

    items: list[ScalingGroupData]
    total_count: int
