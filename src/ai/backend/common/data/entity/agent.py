from typing import NewType
from uuid import UUID

__all__ = ("AgentUUID",)


AgentUUID = NewType("AgentUUID", UUID)
