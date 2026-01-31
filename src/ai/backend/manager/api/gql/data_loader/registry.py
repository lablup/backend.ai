from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any

from aiotools import apartial
from strawberry.dataloader import DataLoader

if TYPE_CHECKING:
    from ai.backend.manager.api.gql.types import StrawberryGQLContext


class DataLoaderRegistry:
    _loader: dict[Callable[..., Any], DataLoader]

    def __init__(self) -> None:
        self._loader = {}

    def get_loader(
        self,
        func: Callable[["StrawberryGQLContext", Any], Awaitable[Any]],
        context: "StrawberryGQLContext",
    ) -> DataLoader:
        loader = self._loader.get(func, None)
        if loader is None:
            new_loader = DataLoader(apartial(func, context))
            self._loader[func] = new_loader
            return new_loader
        return loader
