"""Revision resolver functions."""

from __future__ import annotations

from uuid import UUID

import strawberry
from strawberry import ID, Info
from strawberry.relay import PageInfo
from strawberry.scalars import JSON

from ai.backend.common.dto.manager.v2.deployment.request import (
    ActivateRevisionInput as ActivateRevisionInputDTO,
)
from ai.backend.common.dto.manager.v2.deployment.request import AdminSearchRevisionsInput
from ai.backend.manager.api.gql.base import encode_cursor, resolve_global_id
from ai.backend.manager.api.gql.deployment.types.deployment import ModelDeployment
from ai.backend.manager.api.gql.deployment.types.revision import (
    ActivateRevisionInputGQL,
    ActivateRevisionPayloadGQL,
    AddRevisionInput,
    AddRevisionPayload,
    ModelRevision,
    ModelRevisionConnection,
    ModelRevisionEdge,
    ModelRevisionFilter,
    ModelRevisionOrderBy,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.data.deployment.inference_runtime_config import (
    MOJORuntimeConfig,
    NVDIANIMRuntimeConfig,
    SGLangRuntimeConfig,
    VLLMRuntimeConfig,
)

# Query resolvers


@strawberry.field(description="Added in 25.16.0")  # type: ignore[misc]
async def revisions(
    info: Info[StrawberryGQLContext],
    filter: ModelRevisionFilter | None = None,
    order_by: list[ModelRevisionOrderBy] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> ModelRevisionConnection | None:
    """List revisions with optional filtering and pagination (admin, all deployments)."""
    pydantic_filter = filter.to_pydantic() if filter else None
    pydantic_order = [o.to_pydantic() for o in order_by] if order_by else None
    payload = await info.context.adapters.deployment.admin_search_revisions(
        AdminSearchRevisionsInput(
            filter=pydantic_filter,
            order=pydantic_order,
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        )
    )
    nodes = [ModelRevision.from_pydantic(item) for item in payload.items]
    edges = [ModelRevisionEdge(node=node, cursor=encode_cursor(str(node.id))) for node in nodes]
    return ModelRevisionConnection(
        count=payload.total_count,
        edges=edges,
        page_info=PageInfo(
            has_next_page=payload.has_next_page,
            has_previous_page=payload.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
    )


@strawberry.field(description="Added in 25.16.0")  # type: ignore[misc]
async def revision(id: ID, info: Info[StrawberryGQLContext]) -> ModelRevision | None:
    """Get a specific revision by ID."""
    _, revision_id = resolve_global_id(id)
    node = await info.context.adapters.deployment.get_revision(UUID(revision_id))
    return ModelRevision.from_pydantic(node)


@strawberry.field(  # type: ignore[misc]
    description="Added in 25.16.0. Get JSON Schema for inference runtime configuration"
)
async def inference_runtime_config(name: str) -> JSON:
    match name.lower():
        case "vllm":
            return VLLMRuntimeConfig.to_json_schema()
        case "sglang":
            return SGLangRuntimeConfig.to_json_schema()
        case "nvdianim":
            return NVDIANIMRuntimeConfig.to_json_schema()
        case "mojo":
            return MOJORuntimeConfig.to_json_schema()
        case _:
            return {
                "error": "Unknown service name",
            }


@strawberry.field(  # type: ignore[misc]
    description="Added in 25.16.0 Get configuration JSON Schemas for all inference runtimes"
)
async def inference_runtime_configs(info: Info[StrawberryGQLContext]) -> JSON:
    return {
        "vllm": VLLMRuntimeConfig.to_json_schema(),
        "sglang": SGLangRuntimeConfig.to_json_schema(),
        "nvdianim": NVDIANIMRuntimeConfig.to_json_schema(),
        "mojo": MOJORuntimeConfig.to_json_schema(),
    }


# Mutation resolvers


@strawberry.mutation(description="Added in 25.16.0")  # type: ignore[misc]
async def add_model_revision(
    input: AddRevisionInput, info: Info[StrawberryGQLContext]
) -> AddRevisionPayload:
    """Add a model revision to a deployment."""
    payload = await info.context.adapters.deployment.add_revision(input.to_pydantic())
    return AddRevisionPayload(revision=ModelRevision.from_pydantic(payload.revision))


@strawberry.mutation(  # type: ignore[misc]
    description="Added in 25.19.0. Activate a specific revision to be the current revision."
)
async def activate_deployment_revision(
    input: ActivateRevisionInputGQL,
    info: Info[StrawberryGQLContext, None],
) -> ActivateRevisionPayloadGQL:
    """Activate a revision to be the current revision for a deployment."""
    _, deployment_id = resolve_global_id(input.deployment_id)
    _, revision_id = resolve_global_id(input.revision_id)
    payload = await info.context.adapters.deployment.activate_revision(
        ActivateRevisionInputDTO(
            deployment_id=UUID(deployment_id),
            revision_id=UUID(revision_id),
        )
    )
    return ActivateRevisionPayloadGQL(
        deployment=ModelDeployment.from_pydantic(payload.deployment),
        previous_revision_id=ID(str(payload.previous_revision_id))
        if payload.previous_revision_id
        else None,
        activated_revision_id=ID(str(payload.activated_revision_id)),
    )
