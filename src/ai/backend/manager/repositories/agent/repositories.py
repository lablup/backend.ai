from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.agent.repository import AgentRepository
from ai.backend.manager.repositories.types import RepositoryArgs


@dataclass
class AgentRepositories:
    repository: AgentRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        repository = AgentRepository(args.db)

        return cls(
            repository=repository,
        )
