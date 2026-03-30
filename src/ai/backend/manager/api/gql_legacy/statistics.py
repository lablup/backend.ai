from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any
from uuid import UUID

from ai.backend.common.types import SessionId

if TYPE_CHECKING:
    from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
    from ai.backend.manager.api.gql_legacy.schema import GraphQueryContext


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
        """For cases where required to collect kernel metrics in bulk internally"""
        session_ids_str = [str(sess_id) for sess_id in session_ids]
        return await valkey_stat_client.get_session_statistics_batch(session_ids_str)

    @classmethod
    async def batch_load_by_kernel(
        cls,
        ctx: GraphQueryContext,
        session_ids: Sequence[SessionId],
    ) -> Sequence[Mapping[str, Any] | None]:
        """wrapper of `KernelStatistics.batch_load_by_kernel_impl()` for aiodataloader"""
        return await cls.batch_load_by_kernel_impl(ctx.valkey_stat, session_ids)

    @classmethod
    async def batch_load_inference_metrics_by_kernel(
        cls,
        ctx: GraphQueryContext,
        session_ids: Sequence[SessionId],
    ) -> Sequence[Mapping[str, Any] | None]:
        session_ids_str = [str(sess_id) for sess_id in session_ids]
        return await ctx.valkey_live.get_session_statistics_batch(session_ids_str)


class EndpointStatistics:
    @classmethod
    async def batch_load_by_endpoint_impl(
        cls,
        valkey_stat_client: ValkeyStatClient,
        endpoint_ids: Sequence[UUID],
    ) -> Sequence[Mapping[str, Any] | None]:
        endpoint_id_strs = [str(endpoint_id) for endpoint_id in endpoint_ids]
        return await valkey_stat_client.get_inference_app_statistics_batch(endpoint_id_strs)

    @classmethod
    async def batch_load_by_endpoint(
        cls,
        ctx: GraphQueryContext,
        endpoint_ids: Sequence[UUID],
    ) -> Sequence[Mapping[str, Any] | None]:
        return await cls.batch_load_by_endpoint_impl(ctx.valkey_stat, endpoint_ids)

    @classmethod
    async def batch_load_by_replica(
        cls,
        ctx: GraphQueryContext,
        endpoint_replica_ids: Sequence[tuple[UUID, UUID]],
    ) -> Sequence[Mapping[str, Any] | None]:
        endpoint_replica_pairs = [
            (str(endpoint_id), str(replica_id)) for endpoint_id, replica_id in endpoint_replica_ids
        ]
        return await ctx.valkey_stat.get_inference_replica_statistics_batch(endpoint_replica_pairs)
