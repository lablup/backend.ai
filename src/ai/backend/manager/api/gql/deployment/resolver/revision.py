"""Revision resolver functions."""

from __future__ import annotations

from typing import cast
from uuid import UUID

from strawberry import ID, Info
from strawberry.relay import PageInfo
from strawberry.scalars import JSON

from ai.backend.common.dto.manager.v2.deployment.request import (
    AddRevisionOptions as AdapterAddRevisionOptions,
)
from ai.backend.common.dto.manager.v2.deployment.request import (
    AdminSearchRevisionsInput,
)
from ai.backend.manager.api.gql.base import encode_cursor, resolve_global_id
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_mutation,
    gql_root_field,
)
from ai.backend.manager.api.gql.deployment.types.deployment import ModelDeployment
from ai.backend.manager.api.gql.deployment.types.policy import DeploymentPolicyGQL
from ai.backend.manager.api.gql.deployment.types.revision import (
    ActivateRevisionInputGQL,
    ActivateRevisionPayloadGQL,
    AddRevisionInput,
    AddRevisionOptionsGQL,
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


@gql_root_field(
    BackendAIGQLMeta(
        added_version="25.16.0",
        description="List revisions with optional filtering and pagination (admin, all deployments).",
    )
)  # type: ignore[misc]
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


@gql_root_field(
    BackendAIGQLMeta(added_version="25.16.0", description="Get a specific revision by ID.")
)  # type: ignore[misc]
async def revision(id: ID, info: Info[StrawberryGQLContext]) -> ModelRevision | None:
    """Get a specific revision by ID."""
    _, revision_id = resolve_global_id(id)
    node = await info.context.adapters.deployment.get_revision(UUID(revision_id))
    return ModelRevision.from_pydantic(node)


@gql_root_field(
    BackendAIGQLMeta(
        added_version="25.16.0", description="Get JSON Schema for inference runtime configuration"
    )
)  # type: ignore[misc]
async def inference_runtime_config(name: str) -> JSON:
    match name.lower():
        case "vllm":
            return cast(JSON, VLLMRuntimeConfig.to_json_schema())
        case "sglang":
            return cast(JSON, SGLangRuntimeConfig.to_json_schema())
        case "nvdianim":
            return cast(JSON, NVDIANIMRuntimeConfig.to_json_schema())
        case "mojo":
            return cast(JSON, MOJORuntimeConfig.to_json_schema())
        case _:
            return cast(
                JSON,
                {
                    "error": "Unknown service name",
                },
            )


@gql_root_field(
    BackendAIGQLMeta(
        added_version="25.16.0",
        description="Get configuration JSON Schemas for all inference runtimes.",
    )
)  # type: ignore[misc]
async def inference_runtime_configs(info: Info[StrawberryGQLContext]) -> JSON:
    return cast(
        JSON,
        {
            "vllm": VLLMRuntimeConfig.to_json_schema(),
            "sglang": SGLangRuntimeConfig.to_json_schema(),
            "nvdianim": NVDIANIMRuntimeConfig.to_json_schema(),
            "mojo": MOJORuntimeConfig.to_json_schema(),
        },
    )


# Mutation resolvers


@gql_mutation(BackendAIGQLMeta(added_version="25.16.0", description="Add model revision."))  # type: ignore[misc]
async def add_model_revision(
    input: AddRevisionInput,
    info: Info[StrawberryGQLContext],
    options: AddRevisionOptionsGQL | None = None,
) -> AddRevisionPayload:
    """Add a model revision to a deployment."""
    payload = await info.context.adapters.deployment.add_revision(
        input.to_pydantic(),
        options=options.to_pydantic() if options else AdapterAddRevisionOptions(),
    )
    return AddRevisionPayload(revision=ModelRevision.from_pydantic(payload.revision))


@gql_mutation(
    BackendAIGQLMeta(
        added_version="25.19.0",
        description="Activate a specific revision to be the current revision",
    )
)  # type: ignore[misc]
async def activate_deployment_revision(
    input: ActivateRevisionInputGQL,
    info: Info[StrawberryGQLContext, None],
) -> ActivateRevisionPayloadGQL:
    """Activate a revision to be the current revision for a deployment."""
    payload = await info.context.adapters.deployment.activate_revision(input.to_pydantic())
    return ActivateRevisionPayloadGQL(
        deployment=ModelDeployment.from_pydantic(payload.deployment),
        previous_revision_id=ID(str(payload.previous_revision_id))
        if payload.previous_revision_id
        else None,
        activated_revision_id=ID(str(payload.activated_revision_id)),
        deployment_policy=DeploymentPolicyGQL.from_pydantic(payload.deployment_policy),
    )
