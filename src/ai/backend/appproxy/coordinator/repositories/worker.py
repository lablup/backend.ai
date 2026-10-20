from __future__ import annotations

from dataclasses import dataclass

from ai.backend.appproxy.coordinator.models import Worker
from ai.backend.appproxy.coordinator.models.utils import ExtendedAsyncSAEngine
from ai.backend.common.dto.appproxy.v2.ingress.types import IngressAuthority


@dataclass(frozen=True)
class TraefikWorker:
    hostname: str
    wildcard_domain: str | None
    tls_listen: bool


class WorkerRepository:
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    async def get_traefik_worker(self, authority: IngressAuthority) -> TraefikWorker:
        async with self._db.begin_readonly_session() as session:
            worker = await Worker.find_by_authority(session, authority)
            return TraefikWorker(
                hostname=worker.hostname,
                wildcard_domain=worker.wildcard_domain,
                tls_listen=worker.tls_listen,
            )
