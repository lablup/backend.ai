from __future__ import annotations

import asyncio
import ipaddress
import logging
from abc import ABCMeta, abstractmethod

from ai.backend.appproxy.common.config import ContentEncodingConfig
from ai.backend.appproxy.worker.errors.ingress import (
    IngressFrontendNotRegisteredError,
    IngressNotRegisteredError,
)
from ai.backend.appproxy.worker.proxy.backend.base import BaseBackend
from ai.backend.appproxy.worker.types import Circuit, RootContext
from ai.backend.common.dto.appproxy.v2.ingress.types import (
    Ingress,
    IngressAccess,
    IngressFrontend,
    IngressFrontendKey,
)
from ai.backend.logging.structured import StructuredLogger, with_log_context

log = StructuredLogger(logging.getLogger(__spec__.name))


class BaseFrontend[TBackend: BaseBackend](metaclass=ABCMeta):
    root_context: RootContext
    backends: dict[IngressFrontendKey, TBackend]

    def __init__(self, root_context: RootContext) -> None:
        self.root_context = root_context
        self.backends = {}

    # TODO: Drop the circuit once an ingress carries the values the backends read from it.
    async def register_ingress(self, ingress: Ingress, circuit: Circuit | None = None) -> bool:
        metrics = self.root_context.metrics
        frontend_key = ingress.frontend.key()
        backend = await self.initialize_backend(ingress, circuit)
        self.backends[frontend_key] = backend
        # TODO: Use the ingress id once ingresses are stored as their own entity.
        with with_log_context(circuit_id=backend.circuit_id):
            log.debug("registered the ingress of frontend {}", frontend_key)
        metrics.circuit.observe_circuit_creation(protocol=ingress.frontend.protocol.name)
        return True

    async def update_ingress(self, ingress: Ingress) -> None:
        frontend_key = ingress.frontend.key()
        backend = self.backends.get(frontend_key)
        if backend is None:
            log.debug("skipped an ingress update for unregistered frontend {}", frontend_key)
            return
        await backend.update_ingress(ingress)

    async def remove_ingress(self, frontend: IngressFrontend) -> None:
        metrics = self.root_context.metrics
        frontend_key = frontend.key()
        backend = self.backends.get(frontend_key)
        if backend is None:
            log.debug("skipped removing unregistered frontend {}", frontend_key)
            return
        try:
            await self.terminate_backend(backend)
        except Exception:
            # TODO: Use the ingress id once ingresses are stored as their own entity.
            log.exception("failed to terminate the backend", circuit_id=backend.circuit_id)
        finally:
            del self.backends[frontend_key]
            metrics.circuit.observe_circuit_removal(protocol=frontend.protocol.name)

    async def remove_all_ingresses(self) -> None:
        async with asyncio.TaskGroup() as tg:
            for backend in list(self.backends.values()):
                tg.create_task(self.remove_ingress(backend.ingress.frontend))

    async def _read_registered_ingress(self, frontend_key: IngressFrontendKey) -> Ingress:
        try:
            ingress = await self.root_context.ingress_state.reader.get(frontend_key)
        except IngressNotRegisteredError as e:
            raise IngressFrontendNotRegisteredError(
                f"frontend {frontend_key} is not registered"
            ) from e
        if ingress is None:
            raise IngressFrontendNotRegisteredError(f"frontend {frontend_key} was removed")
        return ingress

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
    async def initialize_backend(
        self, ingress: Ingress, circuit: Circuit | None = None
    ) -> TBackend:
        raise NotImplementedError

    @abstractmethod
    async def terminate_backend(self, backend: TBackend) -> None:
        raise NotImplementedError

    @abstractmethod
    def apply_content_encoding_config(self, config: ContentEncodingConfig) -> None:
        raise NotImplementedError
