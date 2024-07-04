import logging
from abc import ABCMeta
from dataclasses import dataclass
from typing import Any

import aiohttp
from yarl import URL

from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.wsproxy.defs import RootContext
from ai.backend.wsproxy.types import Circuit

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]


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
