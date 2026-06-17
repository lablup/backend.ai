from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.app_config_definition.admin_repository import (
    AppConfigDefinitionAdminRepository,
)
from ai.backend.manager.repositories.app_config_definition.repository import (
    AppConfigDefinitionRepository,
)
from ai.backend.manager.repositories.types import RepositoryArgs


@dataclass
class AppConfigDefinitionRepositories:
    repository: AppConfigDefinitionRepository
    admin_repository: AppConfigDefinitionAdminRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        return cls(
            repository=AppConfigDefinitionRepository(args.ops_provider),
            admin_repository=AppConfigDefinitionAdminRepository(args.ops_provider),
        )
