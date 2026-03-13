from __future__ import annotations

from collections.abc import Sequence

from ai.backend.common.types import KernelId
from ai.backend.manager.data.kernel.types import KernelInfo
from ai.backend.manager.repositories.base import BatchQuerier, NoPagination
from ai.backend.manager.repositories.scheduler.options import KernelConditions
from ai.backend.manager.services.session.actions.search_kernel import SearchKernelsAction
from ai.backend.manager.services.session.processors import SessionProcessors


async def load_kernels_by_ids(
    processor: SessionProcessors,
    kernel_ids: Sequence[KernelId],
) -> list[KernelInfo | None]:
    """Batch load kernels by their IDs.

    Args:
        processor: SessionProcessors instance.
        kernel_ids: List of kernel IDs to load.

    Returns:
        List of KernelInfo (or None if not found) in the same order as kernel_ids.
    """
    if not kernel_ids:
        return []

    querier = BatchQuerier(
        pagination=NoPagination(),
        conditions=[KernelConditions.by_ids(kernel_ids)],
    )

    action_result = await processor.search_kernels.wait_for_complete(
        SearchKernelsAction(querier=querier)
    )

    kernel_map: dict[KernelId, KernelInfo] = {kernel.id: kernel for kernel in action_result.data}
    return [kernel_map.get(kernel_id) for kernel_id in kernel_ids]
