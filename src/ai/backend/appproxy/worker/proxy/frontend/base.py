from __future__ import annotations

import asyncio
import logging
from abc import ABCMeta, abstractmethod

from ai.backend.appproxy.common.types import (
    RouteInfo,
)
from ai.backend.appproxy.worker.proxy.backend.base import BaseBackend
from ai.backend.appproxy.worker.types import Circuit, RootContext
from ai.backend.logging import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class BaseFrontend[TBackend: BaseBackend, TCircuitKeyType: (int, str)](metaclass=ABCMeta):
    root_context: RootContext
    circuits: dict[TCircuitKeyType, Circuit]
    backends: dict[TCircuitKeyType, TBackend]
    # Per-slot mutex serializing register_circuit / break_circuit /
    # update_circuit_route_info on the same port or subdomain. Without
    # this, a break parked at terminate_backend can race with a
    # register on the same slot and its finally clause then wipes
    # whatever the register had swapped in, leaving the slot empty.
    _slot_locks: dict[TCircuitKeyType, asyncio.Lock]

    def __init__(self, root_context: RootContext) -> None:
        self.root_context = root_context
        self.circuits = {}
        self.backends = {}
        self._slot_locks = {}

    def _get_slot_lock(self, key: TCircuitKeyType) -> asyncio.Lock:
        if key not in self._slot_locks:
            self._slot_locks[key] = asyncio.Lock()
        return self._slot_locks[key]

    async def register_circuit(self, circuit: Circuit, routes: list[RouteInfo]) -> None:
        metrics = self.root_context.metrics

        key = self.get_circuit_key(circuit)
        async with self._get_slot_lock(key):
            # Build the new backend first so that the slot only ever
            # transitions between two self-consistent states:
            # (old_circuit, old_backend) or (new_circuit, new_backend). A
            # concurrent request going through ensure_slot_middleware must
            # never observe a circuit paired with a backend that belongs
            # to a different circuit.
            new_backend = await self.initialize_backend(circuit, routes)
            old_backend = self.backends.get(key)
            if old_backend is not None:
                log.warning(
                    "Replacing active slot {} circuit {} with circuit {}",
                    key,
                    self.circuits[key].id,
                    circuit.id,
                )
            # Atomic swap: no await between these two assignments so the
            # two dicts cannot be observed in an intermediate state.
            self.circuits[key] = circuit
            self.backends[key] = new_backend
            if old_backend is not None:
                try:
                    await self.terminate_backend(old_backend)
                except Exception:
                    log.exception("Failed to terminate existing backend for slot {}", key)
            log.debug(
                "circuit {} (app:{}, mode: {}) registered",
                circuit.id,
                circuit.app,
                circuit.app_mode,
            )
            metrics.circuit.observe_circuit_creation(protocol=circuit.protocol.name)

    async def update_circuit_route_info(
        self, circuit: Circuit, new_routes: list[RouteInfo]
    ) -> None:
        key = self.get_circuit_key(circuit)
        async with self._get_slot_lock(key):
            if key not in self.circuits:
                log.warning("Tried to update an inactive slot: {}", key)
                return
            if self.circuits[key].id != circuit.id:
                log.warning(
                    "Ignored route update for stale circuit {} on slot {} (active circuit: {})",
                    circuit.id,
                    key,
                    self.circuits[key].id,
                )
                return
            await self.update_backend(self.backends[key], new_routes)
            self.circuits[key].route_info = new_routes

    async def break_circuit(self, circuit: Circuit) -> None:
        metrics = self.root_context.metrics
        key = self.get_circuit_key(circuit)
        async with self._get_slot_lock(key):
            if key not in self.circuits:
                log.warning("Tried to break an inactive slot: {}", key)
                return
            if self.circuits[key].id != circuit.id:
                log.warning(
                    "Ignored removal for stale circuit {} on slot {} (active circuit: {})",
                    circuit.id,
                    key,
                    self.circuits[key].id,
                )
                return
            backend_to_terminate = self.backends[key]
            # Drop the slot references BEFORE awaiting terminate_backend so
            # a concurrent register on the same slot (once it eventually
            # acquires this lock) sees a clean slot instead of stale
            # (circuit, backend) that we are about to delete.
            del self.backends[key]
            del self.circuits[key]
            try:
                await self.terminate_backend(backend_to_terminate)
            except Exception:
                log.exception("Failed to terminate backend for circuit {}", key)
            metrics.circuit.observe_circuit_removal(protocol=circuit.protocol.name)

    async def terminate_all_circuits(self) -> None:
        async with asyncio.TaskGroup() as tg:
            for circuit in list(self.circuits.values()):
                tg.create_task(self.break_circuit(circuit))

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
    def get_circuit_key(self, circuit: Circuit) -> TCircuitKeyType:
        raise NotImplementedError
