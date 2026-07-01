from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any
from uuid import UUID

from ai.backend.common.types import SessionId

if TYPE_CHECKING:
    from ai.backend.common.clients.valkey_client.valkey_live.client import ValkeyLiveClient
    from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient


__all__ = (
    "KernelStatistics",
    "EndpointStatistics",
)


class KernelStatistics:
    @classmethod
    async def batch_load_by_kernel_impl(
        cls,
        valkey_stat_client: ValkeyStatClient,
        session_ids: Sequence[SessionId],
    ) -> Sequence[Mapping[str, Any] | None]:
        """For cases where required to collect kernel metrics in bulk internally."""
        session_ids_str = [str(sess_id) for sess_id in session_ids]
        return await valkey_stat_client.get_session_statistics_batch(session_ids_str)

    @classmethod
    async def batch_load_inference_metrics_by_kernel(
        cls,
        valkey_live_client: ValkeyLiveClient,
        session_ids: Sequence[SessionId],
    ) -> Sequence[Mapping[str, Any] | None]:
        session_ids_str = [str(sess_id) for sess_id in session_ids]
        return await valkey_live_client.get_session_statistics_batch(session_ids_str)


class EndpointStatistics:
    @classmethod
    async def batch_load_by_endpoint_impl(
        cls,
        valkey_stat_client: ValkeyStatClient,
        endpoint_ids: Sequence[UUID],
    ) -> Sequence[Mapping[str, Any] | None]:
        endpoint_id_strs = [str(endpoint_id) for endpoint_id in endpoint_ids]
        return await valkey_stat_client.get_inference_app_statistics_batch(endpoint_id_strs)
