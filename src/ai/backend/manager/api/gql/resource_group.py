"""
Federated ResourceGroup (ScalingGroup) type with full field definitions for Strawberry GraphQL.
"""

from datetime import datetime

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
