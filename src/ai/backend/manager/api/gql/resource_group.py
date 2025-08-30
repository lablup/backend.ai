"""
Federated ResourceGroup (ScalingGroup) type with full field definitions for Strawberry GraphQL.
"""

from datetime import datetime, timedelta
from typing import cast
from uuid import UUID

import strawberry
from strawberry.relay import Node, NodeID

from .base import JSONString


@strawberry.type
class ResourceGroup(Node):
    id: NodeID

    name: str
    description: str
    is_active: bool
    is_public: bool
    created_at: datetime
    wsproxy_addr: str
    wsproxy_api_token: str
    driver: str
    driver_opts: JSONString
    scheduler: str
    scheduler_opts: JSONString
    use_host_network: bool


mock_resource_group_1 = ResourceGroup(
    id=UUID("1bd4a689-8dab-4355-aadd-9957932d896a"),
    name="gpu-cluster-01",
    description="Primary GPU cluster for inference",
    is_active=True,
    is_public=True,
    created_at=datetime.now() - timedelta(days=100),
    wsproxy_addr="http://proxy-01.backend.ai:5050",
    wsproxy_api_token="mock-token-01",
    driver="cuda",
    driver_opts=cast(JSONString, "{}"),
    scheduler="fifo",
    scheduler_opts=cast(JSONString, "{}"),
    use_host_network=False,
)

mock_resource_group_2 = ResourceGroup(
    id=UUID("0cc27c4c-7fa1-49ae-aa53-9c485205c78b"),
    name="gpu-cluster-02",
    description="Secondary GPU cluster for inference",
    is_active=True,
    is_public=False,
    created_at=datetime.now() - timedelta(days=80),
    wsproxy_addr="http://proxy-02.backend.ai:5050",
    wsproxy_api_token="mock-token-02",
    driver="cuda",
    driver_opts=cast(JSONString, "{}"),
    scheduler="lifo",
    scheduler_opts=cast(JSONString, "{}"),
    use_host_network=False,
)

mock_resource_group_3 = ResourceGroup(
    id=UUID("135f7fd4-60fc-4b0d-9913-f3497d730b31"),
    name="cpu-cluster-01",
    description="CPU cluster for development",
    is_active=True,
    is_public=True,
    created_at=datetime.now() - timedelta(days=60),
    wsproxy_addr="http://proxy-03.backend.ai:5050",
    wsproxy_api_token="mock-token-03",
    driver="cpu",
    driver_opts=cast(JSONString, "{}"),
    scheduler="drf",
    scheduler_opts=cast(JSONString, "{}"),
    use_host_network=False,
)

mock_resource_group_4 = ResourceGroup(
    id=UUID("f4ea16a1-d6cf-41b2-ad0a-d2093658ec59"),
    name="default-cluster",
    description="Default resource group",
    is_active=True,
    is_public=True,
    created_at=datetime.now(),
    wsproxy_addr="http://proxy.backend.ai:5050",
    wsproxy_api_token="default-token",
    driver="auto",
    driver_opts=cast(JSONString, "{}"),
    scheduler="fifo",
    scheduler_opts=cast(JSONString, "{}"),
    use_host_network=False,
)

mock_resource_group_5 = ResourceGroup(
    id=UUID("b2a2c037-f45f-4945-91fb-1b4ff90b0939"),
    name="default-cluster",
    description="Default resource group",
    is_active=True,
    is_public=True,
    created_at=datetime.now(),
    wsproxy_addr="http://proxy.backend.ai:5050",
    wsproxy_api_token="default-token",
    driver="auto",
    driver_opts=cast(JSONString, "{}"),
    scheduler="fifo",
    scheduler_opts=cast(JSONString, "{}"),
    use_host_network=False,
)
