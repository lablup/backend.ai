from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.client_ip_masking.repository import ClientIPMaskingRepository
from ai.backend.manager.repositories.types import RepositoryArgs


@dataclass
class ClientIPMaskingRepositories:
    repository: ClientIPMaskingRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        return cls(repository=ClientIPMaskingRepository(args.db))
