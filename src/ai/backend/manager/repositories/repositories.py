from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.image.repositories import ImageRepositories, RepositoryArgs


@dataclass
class Repositories:
    image: ImageRepositories

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        image_repositories = ImageRepositories.create(args)

        return cls(
            image=image_repositories,
        )
