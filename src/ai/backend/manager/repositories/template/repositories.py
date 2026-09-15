from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Self

from ai.backend.manager.repositories.ops.v2.share.provider import ShareOpsProvider

if TYPE_CHECKING:
    from ai.backend.manager.repositories.types import RepositoryArgs

from .repository import TemplateRepository


@dataclass
class TemplateRepositories:
    repository: TemplateRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        return cls(
            repository=TemplateRepository(db=args.db, ops_provider=ShareOpsProvider(args.db)),
        )
