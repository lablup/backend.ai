from typing import NewType
from uuid import UUID

__all__ = ("DeploymentID",)


DeploymentID = NewType("DeploymentID", UUID)
