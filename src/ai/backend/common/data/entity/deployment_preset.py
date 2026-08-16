from typing import NewType
from uuid import UUID

__all__ = ("DeploymentPresetID",)


DeploymentPresetID = NewType("DeploymentPresetID", UUID)
