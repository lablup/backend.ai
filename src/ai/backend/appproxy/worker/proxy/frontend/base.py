from __future__ import annotations

import asyncio
import ipaddress
import logging
from abc import ABCMeta, abstractmethod

from ai.backend.appproxy.common.config import ContentEncodingConfig
from ai.backend.appproxy.common.types import (
    RouteInfo,
)
from ai.backend.appproxy.worker.errors.ingress import IngressNotRegisteredError
from ai.backend.appproxy.worker.proxy.backend.base import BaseBackend
from ai.backend.appproxy.worker.types import Circuit, RootContext
from ai.backend.common.dto.appproxy.v2.ingress.types import Ingress, IngressAccess, IngressFrontend
from ai.backend.logging.structured import StructuredLogger, with_log_context

log = StructuredLogger(logging.getLogger(__spec__.name))


class BaseFrontend[TBackend: BaseBackend, TCircuitKeyType: (int, str)](metaclass=ABCMeta):
    root_context: RootContext
    backends: dict[TCircuitKeyType, TBackend]

    def __init__(self, root_context: RootContext) -> None:
        self.root_context = root_context
        self.backends = {}

    async def register_circuit(self, circuit: Circuit, routes: list[RouteInfo]) -> None:
        metrics = self.root_context.metrics

        key = self.get_circuit_key(circuit)
        with with_log_context(circuit_id=circuit.id):
            self.backends[key] = await self.initialize_backend(circuit, routes)
            log.debug("circuit registered (app: {}, mode: {})", circuit.app, circuit.app_mode)
        metrics.circuit.observe_circuit_creation(protocol=circuit.protocol.name)

    async def update_circuit_route_info(
        self, circuit: Circuit, new_routes: list[RouteInfo]
    ) -> None:
        key = self.get_circuit_key(circuit)
        backend = self.backends.get(key)
        if backend is None:
            log.debug("skipped a route update for an inactive slot {}", key)
            return
        await self.update_backend(backend, new_routes)
        backend.circuit.route_info = new_routes

    async def break_circuit(self, circuit: Circuit) -> None:
        metrics = self.root_context.metrics
        key = self.get_circuit_key(circuit)
        backend = self.backends.get(key)
        if backend is None:
            log.debug("skipped breaking an inactive slot {}", key)
            return
        try:
            await self.terminate_backend(backend)
        except Exception:
            log.exception("failed to terminate the circuit backend", circuit_id=circuit.id)
        finally:
            del self.backends[key]
            metrics.circuit.observe_circuit_removal(protocol=circuit.protocol.name)

    async def terminate_all_circuits(self) -> None:
        async with asyncio.TaskGroup() as tg:
            for backend in list(self.backends.values()):
                tg.create_task(self.break_circuit(backend.circuit))

    async def _read_ingress(self, frontend: IngressFrontend) -> Ingress | None:
        try:
            return await self.root_context.ingress_state.reader.get(frontend.key())
        except IngressNotRegisteredError:
            return None

    @staticmethod
    def _is_client_ip_allowed(client_ip: str | None, access: IngressAccess) -> bool:
        if not access.allowed_client_ips:
            return True
        if not client_ip:
            return False
        try:
            client_address = ipaddress.ip_address(client_ip)
        except ValueError:
            return False
        return any(client_address in network for network in access.allowed_client_ips)

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
    def apply_content_encoding_config(self, config: ContentEncodingConfig) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_circuit_key(self, circuit: Circuit) -> TCircuitKeyType:
        raise NotImplementedError
