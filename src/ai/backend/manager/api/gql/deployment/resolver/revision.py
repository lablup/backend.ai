"""Revision resolver functions."""

from __future__ import annotations

from typing import Optional
from uuid import UUID

import strawberry
from strawberry import ID, Info
from strawberry.scalars import JSON

from ai.backend.manager.api.gql.base import resolve_global_id
from ai.backend.manager.api.gql.deployment.fetcher.revision import fetch_revisions
from ai.backend.manager.api.gql.deployment.types.deployment import ModelDeployment
from ai.backend.manager.api.gql.deployment.types.revision import (
    ActivateRevisionInputGQL,
    ActivateRevisionPayloadGQL,
    AddRevisionInput,
    AddRevisionPayload,
    CreateRevisionInput,
    CreateRevisionPayload,
    ModelRevision,
    ModelRevisionConnection,
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
from ai.backend.manager.services.deployment.actions.model_revision.add_model_revision import (
    AddModelRevisionAction,
)
from ai.backend.manager.services.deployment.actions.model_revision.create_model_revision import (
    CreateModelRevisionAction,
)
from ai.backend.manager.services.deployment.actions.model_revision.get_revision_by_id import (
    GetRevisionByIdAction,
)
from ai.backend.manager.services.deployment.actions.revision_operations.activate_revision import (
    ActivateRevisionAction,
)

# Query resolvers


@strawberry.field(description="Added in 25.16.0")
async def revisions(
    info: Info[StrawberryGQLContext],
    filter: Optional[ModelRevisionFilter] = None,
    order_by: Optional[list[ModelRevisionOrderBy]] = None,
    before: Optional[str] = None,
    after: Optional[str] = None,
    first: Optional[int] = None,
    last: Optional[int] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> ModelRevisionConnection:
    """List revisions with optional filtering and pagination."""
    return await fetch_revisions(
        info=info,
        filter=filter,
        order_by=order_by,
        before=before,
        after=after,
        first=first,
        last=last,
        limit=limit,
        offset=offset,
    )


@strawberry.field(description="Added in 25.16.0")
async def revision(id: ID, info: Info[StrawberryGQLContext]) -> ModelRevision:
    """Get a specific revision by ID."""
    _, revision_id = resolve_global_id(id)
    processor = info.context.processors.deployment
    result = await processor.get_revision_by_id.wait_for_complete(
        GetRevisionByIdAction(revision_id=UUID(revision_id))
    )
    return ModelRevision.from_dataclass(result.data)


@strawberry.field(
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


@strawberry.field(
    description="Added in 25.16.0 Get configuration JSON Schemas for all inference runtimes"
)
async def inference_runtime_configs(info: Info[StrawberryGQLContext]) -> JSON:
    all_configs = {
        "vllm": VLLMRuntimeConfig.to_json_schema(),
        "sglang": SGLangRuntimeConfig.to_json_schema(),
        "nvdianim": NVDIANIMRuntimeConfig.to_json_schema(),
        "mojo": MOJORuntimeConfig.to_json_schema(),
    }

    return all_configs


# Mutation resolvers


@strawberry.mutation(description="Added in 25.16.0")
async def add_model_revision(
    input: AddRevisionInput, info: Info[StrawberryGQLContext]
) -> AddRevisionPayload:
    """Add a model revision to a deployment."""
    processor = info.context.processors.deployment
    result = await processor.add_model_revision.wait_for_complete(
        AddModelRevisionAction(
            model_deployment_id=UUID(input.deployment_id), adder=input.to_model_revision_creator()
        )
    )

    return AddRevisionPayload(revision=ModelRevision.from_dataclass(result.revision))


@strawberry.mutation(
    description="Added in 25.16.0. Create model revision which is not attached to any deployment."
)
async def create_model_revision(
    input: CreateRevisionInput, info: Info[StrawberryGQLContext]
) -> CreateRevisionPayload:
    """Create a new model revision without attaching it to any deployment."""
    processor = info.context.processors.deployment
    result = await processor.create_model_revision.wait_for_complete(
        CreateModelRevisionAction(creator=input.to_model_revision_creator())
    )

    return CreateRevisionPayload(revision=ModelRevision.from_dataclass(result.revision))


@strawberry.mutation(
    description="Added in 25.19.0. Activate a specific revision to be the current revision."
)
async def activate_deployment_revision(
    input: ActivateRevisionInputGQL,
    info: Info[StrawberryGQLContext, None],
) -> ActivateRevisionPayloadGQL:
    """Activate a revision to be the current revision for a deployment."""
    _, deployment_id = resolve_global_id(input.deployment_id)
    _, revision_id = resolve_global_id(input.revision_id)

    processor = info.context.processors.deployment
    result = await processor.activate_revision.wait_for_complete(
        ActivateRevisionAction(
            deployment_id=UUID(deployment_id),
            revision_id=UUID(revision_id),
        )
    )

    return ActivateRevisionPayloadGQL(
        deployment=ModelDeployment.from_dataclass(result.deployment),
        previous_revision_id=(
            ID(str(result.previous_revision_id)) if result.previous_revision_id else None
        ),
        activated_revision_id=ID(str(result.activated_revision_id)),
    )
