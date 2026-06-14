from typing import NewType
from uuid import UUID

__all__ = ("AppConfigPolicyID",)


AppConfigPolicyID = NewType("AppConfigPolicyID", UUID)
