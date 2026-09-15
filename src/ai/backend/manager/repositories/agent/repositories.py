from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.agent.repository import AgentRepository
from ai.backend.manager.repositories.ops.v2.share.provider import ShareOpsProvider
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
            args.valkey_stat_client,
            args.config_provider,
            ShareOpsProvider(args.db),
        )

        return cls(
            repository=repository,
        )
