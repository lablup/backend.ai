from collections.abc import Sequence
from dataclasses import dataclass

from ai.backend.common.data.entity.project import ProjectID


@dataclass(frozen=True)
class DefaultContainerRegistryQuery:
    project_ids: Sequence[ProjectID]
