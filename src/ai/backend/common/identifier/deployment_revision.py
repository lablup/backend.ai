from typing import NewType
from uuid import UUID

__all__ = ("DeploymentRevisionID",)


DeploymentRevisionID = NewType("DeploymentRevisionID", UUID)
