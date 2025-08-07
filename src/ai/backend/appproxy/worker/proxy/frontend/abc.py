import logging
from abc import ABCMeta, abstractmethod
from typing import Generic, TypeVar

from ai.backend.appproxy.common.logging_utils import BraceStyleAdapter
from ai.backend.appproxy.common.types import (
    RouteInfo,
)
from ai.backend.appproxy.worker.types import Circuit, RootContext, TCircuitKey

from ..backend.abc import AbstractBackend

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]

TBackend = TypeVar("TBackend", bound=AbstractBackend)


class AbstractFrontend(Generic[TBackend, TCircuitKey], metaclass=ABCMeta):
    root_context: RootContext
    circuits: dict[TCircuitKey, Circuit]
    backends: dict[TCircuitKey, TBackend]

    def __init__(self, root_context: RootContext) -> None:
        self.root_context = root_context
        self.circuits = {}
        self.backends = {}

    async def register_circuit(self, circuit: Circuit, routes: list[RouteInfo]) -> None:
        metrics = self.root_context.metrics

        key = self.get_circuit_key(circuit)
        self.circuits[key] = circuit
        self.backends[key] = await self.initialize_backend(circuit, routes)
        log.debug(
            "circuit {} (app:{}, mode: {}) registered", circuit.id, circuit.app, circuit.app_mode
        )

        metrics.circuit.observe_circuit_creation(protocol=circuit.protocol.name)

    async def update_circuit_route_info(
        self, circuit: Circuit, new_routes: list[RouteInfo]
    ) -> None:
        key = self.get_circuit_key(circuit)
        assert key in self.circuits, "Slot not active"
        await self.update_backend(self.backends[key], new_routes)

    async def break_circuit(self, circuit: Circuit) -> None:
        metrics = self.root_context.metrics

        key = self.get_circuit_key(circuit)
        assert key in self.circuits, "Slot not active"
        await self.terminate_backend(self.backends[key])
        del self.backends[key]
        del self.circuits[key]

        metrics.circuit.observe_circuit_removal(protocol=circuit.protocol.name)

    async def terminate_all_circuits(self) -> None:
        for circuit in list(self.circuits.values()):
            await self.break_circuit(circuit)

    @abstractmethod
    async def start(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def stop(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def initialize_backend(self, circuit: Circuit, routes: list[RouteInfo]) -> TBackend:
        raise NotImplementedError

    @abstractmethod
    async def update_backend(self, backend: TBackend, routes: list[RouteInfo]) -> TBackend:
        raise NotImplementedError

    @abstractmethod
    async def terminate_backend(self, backend: TBackend) -> None:
        raise NotImplementedError

    @abstractmethod
    async def list_inactive_circuits(self, threshold: int) -> list[Circuit]:
        raise NotImplementedError

    @abstractmethod
    def get_circuit_key(self, circuit: Circuit) -> TCircuitKey:
        raise NotImplementedError
