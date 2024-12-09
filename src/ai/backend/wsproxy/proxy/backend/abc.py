import logging
from abc import ABCMeta, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, TypeVar

import aiohttp
from yarl import URL

from ai.backend.logging import BraceStyleAdapter

from ...defs import RootContext
from ...types import Circuit

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@dataclass
class HttpRequest:
    method: str
    path: str | URL
    headers: dict[str, Any]
    body: aiohttp.StreamReader


class AbstractBackend(metaclass=ABCMeta):
    root_context: RootContext
    circuit: Circuit

    def __init__(self, root_context: RootContext, circuit: Circuit) -> None:
        self.root_context = root_context
        self.circuit = circuit


TRoute = TypeVar("TRoute")


class AbstractRouteSelector(metaclass=ABCMeta):
    @abstractmethod
    def select_route(self, routes: Sequence[TRoute]) -> TRoute:
        raise NotImplementedError
