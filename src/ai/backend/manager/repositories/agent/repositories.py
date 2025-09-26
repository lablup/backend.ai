from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.agent.repository import AgentRepository
from ai.backend.manager.repositories.types import RepositoryArgs


@dataclass
class AgentRepositories:
    repository: AgentRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
<<<<<<< HEAD
        repository = AgentRepository(
            args.db,
            args.valkey_image_client,
            args.valkey_live_client,
            args.config_provider,
        )
=======
        repository = AgentRepository(args.db, args.config_provider)
>>>>>>> 523f97e59 (fix missing calc)

        return cls(
            repository=repository,
        )
