import logging
from abc import ABCMeta, abstractmethod
from typing import Generic, TypeVar
from uuid import UUID

from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.wsproxy.defs import RootContext
from ai.backend.wsproxy.exceptions import ObjectNotFound
from ai.backend.wsproxy.types import (
    Circuit,
    RouteInfo,
    TCircuitKey,
)

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

    def get_circuit_by_endpoint_id(self, endpoint_id: UUID) -> Circuit:
        for _, circuit in self.circuits.items():
            if circuit.endpoint_id == endpoint_id:
                return circuit
        raise ObjectNotFound(object_name="Circuit")

    def get_circuit_by_id(self, id: UUID) -> Circuit:
        for _, circuit in self.circuits.items():
            if circuit.id == id:
                return circuit
        raise ObjectNotFound(object_name="Circuit")

    async def register_circuit(self, circuit: Circuit, routes: list[RouteInfo]) -> None:
        key = self.get_circuit_key(circuit)
        self.circuits[key] = circuit
        self.backends[key] = await self.initialize_backend(circuit, routes)
        log.info(
            "circuit {} (app:{}, mode: {}) registered", circuit.id, circuit.app, circuit.app_mode
        )

    async def update_circuit_route_info(
        self, circuit: Circuit, new_routes: list[RouteInfo]
    ) -> None:
        key = self.get_circuit_key(circuit)
        assert key in self.circuits, "Slot not active"
        await self.update_backend(self.backends[key], new_routes)

    async def break_circuit(self, circuit: Circuit) -> None:
        key = self.get_circuit_key(circuit)
        assert key in self.circuits, "Slot not active"
        await self.terminate_backend(self.backends[key])
        del self.backends[key]
        del self.circuits[key]
        log.info(
            "circuit {} (app:{}, mode: {}) unregistered", circuit.id, circuit.app, circuit.app_mode
        )

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
    def get_circuit_key(self, circuit: Circuit) -> TCircuitKey:
        raise NotImplementedError
