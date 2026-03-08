"""Statistics batch-loading helpers for Valkey stat data.

These are layer-neutral functions that can be used by both
the repository layer and the GQL layer.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any
from uuid import UUID

from ai.backend.common.types import SessionId

if TYPE_CHECKING:
    from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient


async def batch_load_kernel_statistics(
    valkey_stat_client: ValkeyStatClient,
    session_ids: Sequence[SessionId],
) -> Sequence[Mapping[str, Any] | None]:
    """Batch-load kernel/session statistics from Valkey."""
    session_ids_str = [str(sess_id) for sess_id in session_ids]
    return await valkey_stat_client.get_session_statistics_batch(session_ids_str)


async def batch_load_endpoint_statistics(
    valkey_stat_client: ValkeyStatClient,
    endpoint_ids: Sequence[UUID],
) -> Sequence[Mapping[str, Any] | None]:
    """Batch-load endpoint statistics from Valkey."""
    endpoint_id_strs = [str(endpoint_id) for endpoint_id in endpoint_ids]
    return await valkey_stat_client.get_inference_app_statistics_batch(endpoint_id_strs)
