"""
Federated User type with full field definitions for Strawberry GraphQL.
"""

from datetime import datetime

import strawberry
from strawberry.relay import Node, NodeID


@strawberry.type(name="UserDetail")
class User(Node):
    id: NodeID  # Inherits from Node

    username: str = strawberry.field(description="Unique username of the user.")
    email: str = strawberry.field(description="Unique email of the user.")
    need_password_change: bool = strawberry.field()
    full_name: str = strawberry.field()
    description: str = strawberry.field()
    status: str = strawberry.field(
        description="The status is one of `active`, `inactive`, `deleted` or `before-verification`.",
    )
    status_info: str = strawberry.field(description="Additional information of user status.")
    created_at: datetime = strawberry.field()
    modified_at: datetime = strawberry.field()
    domain_name: str = strawberry.field()
    role: str = strawberry.field(
        description="The role is one of `user`, `admin`, `superadmin` or `monitor`."
    )
    resource_policy: str = strawberry.field()
    allowed_client_ip: list[str] = strawberry.field()
    totp_activated: bool = strawberry.field()
    totp_activated_at: datetime = strawberry.field()
    sudo_session_enabled: bool = strawberry.field()
    container_uid: int = strawberry.field(
        default=None,
        description="Added in 25.2.0. The user ID (UID) assigned to processes running inside the container.",
    )
    container_main_gid: int = strawberry.field(
        description="Added in 25.2.0. The primary group ID (GID) assigned to processes running inside the container.",
    )
    container_gids: list[int] = strawberry.field(
        description="Added in 25.2.0. Supplementary group IDs assigned to processes running inside the container.",
    )
