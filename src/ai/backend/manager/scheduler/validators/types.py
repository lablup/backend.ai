from dataclasses import dataclass
from datetime import datetime
from typing import Mapping, Optional

from ai.backend.common.types import (
    ResourceSlot,
    SlotName,
    SlotTypes,
)
from ai.backend.manager.data.resource.types import (
    DomainResourcePolicyData,
    GroupResourcePolicyData,
    KeyPairResourcePolicyData,
)
from ai.backend.manager.data.session.types import SessionData, SessionDependencyData
from ai.backend.manager.data.user.types import UserData


@dataclass
class ValidatorContext:
    """Context data for scheduler validators containing pre-fetched data from repositories"""

    # Session data
    session_data: SessionData
    session_starts_at: Optional[datetime]
    session_dependencies: list[SessionDependencyData]
    pending_sessions: list[SessionData]

    # Resource policies
    keypair_resource_policy: KeyPairResourcePolicyData
    user_main_keypair_resource_policy: Optional[KeyPairResourcePolicyData]
    group_resource_policy: GroupResourcePolicyData
    domain_resource_policy: DomainResourcePolicyData

    # Current resource usage (occupancy)
    keypair_concurrency_used: int
    keypair_occupancy: ResourceSlot
    user_occupancy: ResourceSlot
    group_occupancy: ResourceSlot
    domain_occupancy: ResourceSlot

    # Additional data
    group_name: str
    user_data: UserData

    # Scheduler context
    known_slot_types: Mapping[SlotName, SlotTypes]
