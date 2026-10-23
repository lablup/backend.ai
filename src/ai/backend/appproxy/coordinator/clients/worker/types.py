from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TraefikWorker:
    hostname: str
    wildcard_domain: str | None
    tls_listen: bool
