from dataclasses import dataclass

from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

from .admin_repository import AdminAgentRegistryRepository
from .repository import AgentRegistryRepository


@dataclass
class AgentRegistryRepositories:
    repository: AgentRegistryRepository
    admin_repository: AdminAgentRegistryRepository

    @classmethod
    def create(cls, db: ExtendedAsyncSAEngine) -> "AgentRegistryRepositories":
        return cls(
            repository=AgentRegistryRepository(db),
            admin_repository=AdminAgentRegistryRepository(db),
        )
