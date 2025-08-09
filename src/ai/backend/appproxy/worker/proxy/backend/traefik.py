from ai.backend.appproxy.common.types import RouteInfo

from ...types import Circuit, RootContext
from .base import BaseBackend


class TraefikBackend(BaseBackend):
    worker_circuit: Circuit

    def __init__(self, context: RootContext, circuit: Circuit, routes: list[RouteInfo]) -> None:
        super().__init__(context, circuit)

        self.routes = routes
        self.worker_circuit = circuit
