from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence

from ai.backend.common.dto.appproxy.v2.ingress.types import Ingress, IngressFrontendKey, IngressKey


class IngressReader(ABC):
    @abstractmethod
    async def get(self, frontend_key: IngressFrontendKey) -> Ingress | None:
        """None when this layer does not hold the key; IngressNotFoundError when it is known missing."""
        raise NotImplementedError

    @abstractmethod
    async def get_all(self) -> list[Ingress]:
        """Every ingress of the worker's authority."""
        raise NotImplementedError


class IngressWriter(ABC):
    @abstractmethod
    async def apply(self, ingresses: Sequence[Ingress]) -> None:
        raise NotImplementedError

    @abstractmethod
    async def remove(self, keys: Sequence[IngressKey]) -> None:
        raise NotImplementedError

    @abstractmethod
    async def replace_all(self, ingresses: Sequence[Ingress]) -> None:
        raise NotImplementedError
