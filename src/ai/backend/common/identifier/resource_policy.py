from typing import NewType
from uuid import UUID

__all__ = (
    "KeyPairResourcePolicyUUID",
    "ProjectResourcePolicyUUID",
    "UserResourcePolicyUUID",
)


# The three policies key on ``name`` — that is what keypairs/users/groups
# reference — so the UUID below is the unique alternate key that gives each row
# its ``EntityID``, not its primary key.
KeyPairResourcePolicyUUID = NewType("KeyPairResourcePolicyUUID", UUID)
UserResourcePolicyUUID = NewType("UserResourcePolicyUUID", UUID)
ProjectResourcePolicyUUID = NewType("ProjectResourcePolicyUUID", UUID)
