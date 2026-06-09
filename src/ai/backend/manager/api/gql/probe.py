"""Test-only probe query for observing DataLoader batch coalescing.

``loadedBatchIds`` resolves a single id through the shared ``loaded_batch_ids_loader``
and returns the full batch of ids that load was coalesced into, plus the user observed
by the batch function. Concurrent requests that share the process-wide ``DataLoaders``
instance therefore reveal, in their responses, that their loads landed in one batch.

This exists to make the batching/authorization behaviour testable end-to-end; it is not
intended for production use.
"""

from __future__ import annotations

import strawberry
from strawberry import Info

from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.decorators import BackendAIGQLMeta, gql_root_field
from ai.backend.manager.api.gql.types import StrawberryGQLContext


@strawberry.type
class BatchProbeResult:
    batch: list[str]
    seen_user: str | None


@gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Probe: returns the DataLoader batch a single load was coalesced into.",
    )
)  # type: ignore[misc]
async def loaded_batch_ids(
    info: Info[StrawberryGQLContext],
    id: strawberry.ID,
) -> BatchProbeResult:
    loaders = info.context.data_loaders
    barrier = loaders.probe_barrier
    if barrier is not None:
        await barrier.wait()
    data = await loaders.loaded_batch_ids_loader.load(str(id))
    return BatchProbeResult(batch=data.batch, seen_user=data.seen_user)


@gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Probe: owner-only authz check inside load_fn; demonstrates cache bypass.",
    )
)  # type: ignore[misc]
async def authz_probe(
    info: Info[StrawberryGQLContext],
    id: strawberry.ID,
) -> str:
    return await info.context.data_loaders.authz_probe_loader.load(str(id))
