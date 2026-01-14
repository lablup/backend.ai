from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from .actions.search import SearchKernelsAction, SearchKernelsActionResult

if TYPE_CHECKING:
    from ai.backend.manager.repositories.kernel import KernelRepository

__all__ = ("KernelService",)


@dataclass
class KernelService:
    """Service for kernel operations."""

    _repository: KernelRepository

    def __init__(self, repository: KernelRepository) -> None:
        self._repository = repository

    async def search(self, action: SearchKernelsAction) -> SearchKernelsActionResult:
        """Search kernels with querier pattern."""
        result = await self._repository.search(action.querier)
        return SearchKernelsActionResult(
            data=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )
