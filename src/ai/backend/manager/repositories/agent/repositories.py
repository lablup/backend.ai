from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.agent.repository import AgentRepository
from ai.backend.manager.repositories.types import RepositoryArgs


@dataclass
class AgentRepositories:
    repository: AgentRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        repository = AgentRepository(
            args.db,
            args.valkey_image_client,
            args.valkey_live_client,
            args.config_provider,
        )

        return cls(
            repository=repository,
        )
