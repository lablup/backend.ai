from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence

from ai.backend.common.dto.appproxy.v2.ingress.types import Ingress, IngressKey


class AbstractWorkerClient(ABC):
    """Sends ingresses to what serves an authority's traffic: an api-delivery worker node,
    or Traefik when it is enabled."""

    @abstractmethod
    async def upsert(self, ingresses: Sequence[Ingress]) -> None:
        """Compares every ingress with the revision applied for its frontend before applying any,
        and raises without applying one when any is older. An ingress at the applied revision is
        applied again."""
        raise NotImplementedError

    @abstractmethod
    async def remove(self, keys: Sequence[IngressKey]) -> None:
        """Removes the ingress applied for each key whatever its revision; a key with nothing
        applied is skipped."""
        raise NotImplementedError
