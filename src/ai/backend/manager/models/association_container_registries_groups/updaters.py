from dataclasses import dataclass

from ai.backend.common.data.entity.container_registry import ContainerRegistryID
from ai.backend.common.data.entity.project import ProjectID


@dataclass(frozen=True)
class ProjectDefaultRegistryUpdater:
    project_id: ProjectID
    previous_registry_id: ContainerRegistryID | None
    registry_id: ContainerRegistryID | None
