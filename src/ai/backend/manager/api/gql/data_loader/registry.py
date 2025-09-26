from typing import TYPE_CHECKING, Any, Awaitable, Callable

from aiotools import apartial
from strawberry.dataloader import DataLoader

if TYPE_CHECKING:
    from ai.backend.manager.api.gql.types import StrawberryGQLContext


class DataLoaderRegistry:
    _loader: dict[Callable, DataLoader]

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
