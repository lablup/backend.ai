from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence

from ai.backend.common.dto.appproxy.v2.ingress.types import Ingress, IngressKey


class BaseWorkerClient(ABC):
    """Sends ingresses to what serves an authority's traffic: an api-delivery worker node,
    or Traefik when it is enabled."""

    @abstractmethod
    async def upsert(self, ingresses: Sequence[Ingress]) -> None:
        raise NotImplementedError

    @abstractmethod
    async def remove(self, keys: Sequence[IngressKey]) -> None:
        raise NotImplementedError
