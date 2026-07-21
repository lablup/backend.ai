from typing import NewType
from uuid import UUID

__all__ = ("RetentionPolicyID",)


RetentionPolicyID = NewType("RetentionPolicyID", UUID)
