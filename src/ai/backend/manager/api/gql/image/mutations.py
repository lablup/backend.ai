"""
ImageV2 GQL mutations for Strawberry GraphQL.

This module provides GraphQL mutation fields for ImageV2.
"""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

import strawberry
from strawberry import ID, Info

from ai.backend.common.types import ImageID
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.utils import dedent_strip
from ai.backend.manager.data.image.types import ImageType, ResourceLimitInput
from ai.backend.manager.repositories.image.updaters import ImageUpdaterSpec
from ai.backend.manager.services.image.actions.alias_image import (
    AliasImageByIdAction,
)
from ai.backend.manager.services.image.actions.clear_image_custom_resource_limit import (
    ClearImageCustomResourceLimitByIdAction,
)
from ai.backend.manager.services.image.actions.dealias_image import (
    DealiasImageAction,
)
from ai.backend.manager.services.image.actions.forget_image import (
    ForgetImageByIdAction,
)
from ai.backend.manager.services.image.actions.modify_image import (
    ModifyImageByIdAction,
)
from ai.backend.manager.services.image.actions.purge_images import (
    PurgeImageByIdAction,
)
from ai.backend.manager.services.image.actions.set_image_resource_limit import (
    SetImageResourceLimitByIdAction,
)
from ai.backend.manager.services.image.actions.untag_image_from_registry import (
    UntagImageFromRegistryAction,
)
from ai.backend.manager.types import OptionalState, TriState

from .types import ImageV2GQL

# =============================================================================
# Mutation Input Types
# =============================================================================


@strawberry.input(
    name="ForgetImageInput",
    description=dedent_strip("""
    Added in 26.2.0.

    Input for forgetting an image by ID.
    This performs a soft delete, marking the image as DELETED without removing it from the database.
    """),
)
class ForgetImageInputGQL:
    image_id: ID = strawberry.field(description="The UUID of the image to mark as deleted.")


@strawberry.input(
    name="PurgeImageOptions",
    description=dedent_strip("""
    Added in 26.2.0.

    Options for purging an image.
    """),
)
class PurgeImageOptionsGQL:
    remove_from_registry: bool = strawberry.field(
        default=False,
        description="Untag the deleted image from the registry. Only available for HarborV2 registries.",
    )


@strawberry.input(
    name="PurgeImageInput",
    description=dedent_strip("""
    Added in 26.2.0.

    Input for purging an image by ID.
    This permanently removes the image record from the database.
    """),
)
class PurgeImageInputGQL:
    image_id: ID = strawberry.field(description="The UUID of the image to permanently delete.")
    options: PurgeImageOptionsGQL | None = strawberry.field(
        default=None,
        description="Additional options controlling the purge behavior (e.g., registry cleanup).",
    )


@strawberry.input(
    name="AliasImageInput",
    description=dedent_strip("""
    Added in 26.2.0.

    Input for creating an alias for an image by ID.
    Aliases provide user-friendly names to reference images without using the full canonical name.
    """),
)
class AliasImageInputGQL:
    image_id: ID = strawberry.field(description="The UUID of the target image.")
    alias: str = strawberry.field(
        description="The alias string to create (e.g., 'python', 'tensorflow'). Must be unique across all images."
    )


@strawberry.input(
    name="DealiasImageInput",
    description=dedent_strip("""
    Added in 26.2.0.

    Input for removing an alias from an image.
    After removal, the alias can be reused for other images.
    """),
)
class DealiasImageInputGQL:
    alias: str = strawberry.field(
        description="The alias string to remove. Must be an existing alias."
    )


@strawberry.input(
    name="ClearImageResourceLimitInput",
    description=dedent_strip("""
    Added in 26.2.0.

    Input for clearing custom resource limits for an image.
    After clearing, the image will use the default limits specified in its labels.
    """),
)
class ClearImageResourceLimitInputGQL:
    image_id: ID = strawberry.field(
        description="The UUID of the image whose custom resource limits will be cleared."
    )


@strawberry.input(
    name="UntagImageFromRegistryInput",
    description=dedent_strip("""
    Added in 26.2.0.

    Input for untagging an image from its container registry.
    This removes the tag from the remote registry. Currently only supported for HarborV2 registries.
    """),
)
class UntagImageFromRegistryInputGQL:
    image_id: ID = strawberry.field(
        description="The UUID of the image whose tag will be removed from the container registry."
    )


@strawberry.input(
    name="ResourceLimitInput",
    description=dedent_strip("""
    Added in 26.2.0.

    Input for a single resource limit specification.
    """),
)
class ResourceLimitInputGQL:
    slot_name: str = strawberry.field(
        description="The name of the resource slot (e.g., 'cpu', 'mem')."
    )
    min_value: str | None = strawberry.field(
        default=None,
        description="The minimum value for this resource. Use string to represent decimal values.",
    )
    max_value: str | None = strawberry.field(
        default=None,
        description="The maximum value for this resource. Use string to represent decimal values.",
    )


@strawberry.input(
    name="SetImageResourceLimitInput",
    description=dedent_strip("""
    Added in 26.2.0.

    Input for setting custom resource limits for an image.
    This overrides the default limits specified in the image labels.
    """),
)
class SetImageResourceLimitInputGQL:
    image_id: ID = strawberry.field(description="The UUID of the target image.")
    resource_limit: ResourceLimitInputGQL = strawberry.field(
        description="The resource limit specification to apply. Overwrites any existing limit for the same slot.",
    )


@strawberry.input(
    name="ImageLabelInput",
    description=dedent_strip("""
    Added in 26.2.0.

    Input for an image label (key-value pair).
    Labels are used to store metadata about the image, such as runtime requirements,
    supported features, or custom annotations.
    """),
)
class ImageLabelInputGQL:
    key: str = strawberry.field(
        description="The label key (e.g., 'ai.backend.runtime-type', 'ai.backend.service-ports')."
    )
    value: str = strawberry.field(
        description="The label value. Format depends on the key (e.g., JSON array for service-ports)."
    )


@strawberry.input(
    name="ResourceLimitModifyInput",
    description=dedent_strip("""
    Added in 26.2.0.

    Resource limit input for modifying image resource limits.
    Defines the minimum and maximum allowed values for a specific resource slot.
    """),
)
class ResourceLimitModifyInputGQL:
    key: str = strawberry.field(
        description="The resource slot name (e.g., 'cpu', 'mem', 'cuda.shares', 'cuda.device')."
    )
    min: str | None = strawberry.field(
        default=None,
        description="The minimum allowed value as a decimal string (e.g., '1' for 1 CPU core, '1g' for 1GB memory).",
    )
    max: str | None = strawberry.field(
        default=None,
        description="The maximum allowed value as a decimal string (e.g., '4' for 4 CPU cores, '16g' for 16GB memory).",
    )


@strawberry.input(
    name="ModifyImagePropsInput",
    description=dedent_strip("""
    Added in 26.2.0.

    Input for modifying an image's properties.
    All fields are optional; only provided fields will be updated.
    """),
)
class ModifyImagePropsInputGQL:
    name: str | None = strawberry.field(
        default=None,
        description="The human-readable display name for the image (e.g., 'TensorFlow 2.12 on Python 3.10').",
    )
    registry: str | None = strawberry.field(
        default=None,
        description="The container registry hostname where the image is stored (e.g., 'cr.backend.ai', 'docker.io').",
    )
    image: str | None = strawberry.field(
        default=None,
        description="The repository path within the registry (e.g., 'stable/python', 'library/ubuntu').",
    )
    tag: str | None = strawberry.field(
        default=None,
        description="The image tag identifying a specific version (e.g., '3.10-cuda12.1', 'latest').",
    )
    architecture: str | None = strawberry.field(
        default=None,
        description="The CPU architecture the image is built for (e.g., 'x86_64', 'aarch64').",
    )
    is_local: bool | None = strawberry.field(
        default=None,
        description="Whether the image exists only locally and is not pulled from a remote registry.",
    )
    size_bytes: int | None = strawberry.field(
        default=None, description="The total size of the image in bytes."
    )
    type: str | None = strawberry.field(
        default=None,
        description="The image type: 'compute' for user workloads, 'system' for internal use, 'service' for model serving.",
    )
    digest: str | None = strawberry.field(
        default=None,
        description="The SHA256 config digest of the image manifest (e.g., 'sha256:abc123...').",
    )
    labels: list[ImageLabelInputGQL] | None = strawberry.field(
        default=None,
        description="Key-value metadata labels. Replaces all existing labels when provided.",
    )
    supported_accelerators: list[str] | None = strawberry.field(
        default=None,
        description="List of supported accelerator types (e.g., ['cuda', 'rocm']). Set to empty list to clear all accelerators.",
    )
    resource_limits: list[ResourceLimitModifyInputGQL] | None = strawberry.field(
        default=None,
        description="Custom resource limits overriding image defaults. Each entry specifies min/max for a resource slot.",
    )

    def to_updater_spec(self) -> ImageUpdaterSpec:
        """Convert input to ImageUpdaterSpec."""

        def _optional[T](value: T | None) -> OptionalState[T]:
            return OptionalState.update(value) if value is not None else OptionalState.nop()

        # Handle resources
        resources_data: dict[str, dict[str, str]] | None = None
        if self.resource_limits is not None:
            resources_data = {}
            for limit in self.resource_limits:
                limit_data: dict[str, str] = {}
                if limit.min is not None:
                    limit_data["min"] = limit.min
                if limit.max is not None:
                    limit_data["max"] = limit.max
                resources_data[limit.key] = limit_data

        # Handle accelerators
        accelerators_state: TriState[str]
        if self.supported_accelerators is not None:
            if len(self.supported_accelerators) == 0:
                accelerators_state = TriState.nullify()
            else:
                accelerators_state = TriState.update(",".join(self.supported_accelerators))
        else:
            accelerators_state = TriState.nop()

        # Handle labels
        labels: dict[str, str] | None = None
        if self.labels is not None:
            labels = {label.key: label.value for label in self.labels}

        # Handle image type
        image_type: ImageType | None = None
        if self.type is not None:
            image_type = ImageType(self.type)

        return ImageUpdaterSpec(
            name=_optional(self.name),
            registry=_optional(self.registry),
            image=_optional(self.image),
            tag=_optional(self.tag),
            architecture=_optional(self.architecture),
            is_local=_optional(self.is_local),
            size_bytes=_optional(self.size_bytes),
            image_type=_optional(image_type),
            config_digest=_optional(self.digest),
            labels=_optional(labels),
            accelerators=accelerators_state,
            resources=_optional(resources_data),
        )


@strawberry.input(
    name="ModifyImageInput",
    description=dedent_strip("""
    Added in 26.2.0.

    Input for modifying an image by ID.
    Allows batch updating multiple image properties in a single operation.
    """),
)
class ModifyImageInputGQL:
    image_id: ID = strawberry.field(description="The UUID of the target image.")
    props: ModifyImagePropsInputGQL = strawberry.field(
        description="The properties to update. Only non-null fields will be modified."
    )


# =============================================================================
# Mutation Result Types
# =============================================================================


@strawberry.type(
    name="ForgetImageResult",
    description=dedent_strip("""
    Added in 26.2.0.

    Result of forgetting an image by ID. The image is marked as DELETED
    but not removed from the database.
    """),
)
class ForgetImageResultGQL:
    image: ImageV2GQL = strawberry.field(description="The forgotten image.")


@strawberry.type(
    name="PurgeImageResult",
    description=dedent_strip("""
    Added in 26.2.0.

    Result of purging an image by ID. The image is completely removed
    from the database.
    """),
)
class PurgeImageResultGQL:
    image: ImageV2GQL = strawberry.field(description="The purged image data.")


@strawberry.type(
    name="AliasImageResult",
    description=dedent_strip("""
    Added in 26.2.0.

    Result of creating an alias for an image.
    """),
)
class AliasImageResultGQL:
    image_id: ID = strawberry.field(description="The ID of the aliased image.")
    alias: str = strawberry.field(description="The created alias.")


@strawberry.type(
    name="DealiasImageResult",
    description=dedent_strip("""
    Added in 26.2.0.

    Result of removing an alias from an image.
    """),
)
class DealiasImageResultGQL:
    image_id: ID = strawberry.field(description="The ID of the image that had the alias.")
    alias: str = strawberry.field(description="The removed alias.")


@strawberry.type(
    name="ClearImageResourceLimitResult",
    description=dedent_strip("""
    Added in 26.2.0.

    Result of clearing custom resource limits for an image.
    """),
)
class ClearImageResourceLimitResultGQL:
    image: ImageV2GQL = strawberry.field(description="The image with cleared resource limits.")


@strawberry.type(
    name="UntagImageFromRegistryResult",
    description=dedent_strip("""
    Added in 26.2.0.

    Result of untagging an image from its container registry.
    """),
)
class UntagImageFromRegistryResultGQL:
    image: ImageV2GQL = strawberry.field(description="The untagged image.")


@strawberry.type(
    name="SetImageResourceLimitResult",
    description=dedent_strip("""
    Added in 26.2.0.

    Result of setting custom resource limits for an image.
    """),
)
class SetImageResourceLimitResultGQL:
    image: ImageV2GQL = strawberry.field(description="The image with updated resource limits.")


@strawberry.type(
    name="ModifyImageResult",
    description=dedent_strip("""
    Added in 26.2.0.

    Result of modifying an image.
    """),
)
class ModifyImageResultGQL:
    image: ImageV2GQL = strawberry.field(description="The modified image.")


# =============================================================================
# Mutation Functions
# =============================================================================


@strawberry.mutation(  # type: ignore[misc]
    description=dedent_strip("""
    Added in 26.2.0.

    Mark an image as deleted by its ID.

    The image is not removed from the database but its status changes to DELETED.
    This is a soft delete operation.
    """)
)
async def forget_image(
    input: ForgetImageInputGQL,
    info: Info[StrawberryGQLContext],
) -> ForgetImageResultGQL:
    ctx = info.context

    result = await ctx.processors.image.forget_image_by_id.wait_for_complete(
        ForgetImageByIdAction(image_id=ImageID(UUID(input.image_id)))
    )

    return ForgetImageResultGQL(image=ImageV2GQL.from_data(result.image))


@strawberry.mutation(  # type: ignore[misc]
    description=dedent_strip("""
    Added in 26.2.0.

    Completely purge an image by its ID.

    The image is permanently removed from the database. Optionally, the image
    can also be untagged from the container registry (HarborV2 only).
    """)
)
async def purge_image(
    input: PurgeImageInputGQL,
    info: Info[StrawberryGQLContext],
) -> PurgeImageResultGQL:
    ctx = info.context
    image_uuid = UUID(input.image_id)

    result = await ctx.processors.image.purge_image_by_id.wait_for_complete(
        PurgeImageByIdAction(image_id=ImageID(image_uuid))
    )

    if input.options and input.options.remove_from_registry:
        await ctx.processors.image.untag_image_from_registry.wait_for_complete(
            UntagImageFromRegistryAction(image_id=ImageID(image_uuid))
        )

    return PurgeImageResultGQL(image=ImageV2GQL.from_data(result.image))


@strawberry.mutation(  # type: ignore[misc]
    description=dedent_strip("""
    Added in 26.2.0.

    Create an alias for an image by its ID.

    An alias is an alternative name that can be used to reference the image.
    Multiple aliases can be created for the same image.
    """)
)
async def alias_image(
    input: AliasImageInputGQL,
    info: Info[StrawberryGQLContext],
) -> AliasImageResultGQL:
    ctx = info.context

    result = await ctx.processors.image.alias_image_by_id.wait_for_complete(
        AliasImageByIdAction(
            image_id=ImageID(UUID(input.image_id)),
            alias=input.alias,
        )
    )

    return AliasImageResultGQL(
        image_id=ID(str(result.image_id)),
        alias=result.image_alias.alias,
    )


@strawberry.mutation(  # type: ignore[misc]
    description=dedent_strip("""
    Added in 26.2.0.

    Remove an alias from an image.
    """)
)
async def dealias_image(
    input: DealiasImageInputGQL,
    info: Info[StrawberryGQLContext],
) -> DealiasImageResultGQL:
    ctx = info.context

    result = await ctx.processors.image.dealias_image.wait_for_complete(
        DealiasImageAction(alias=input.alias)
    )

    return DealiasImageResultGQL(
        image_id=ID(str(result.image_id)),
        alias=result.image_alias.alias,
    )


@strawberry.mutation(  # type: ignore[misc]
    description=dedent_strip("""
    Added in 26.2.0.

    Clear custom resource limits for an image by its ID.

    This removes any user-defined resource limits and reverts to the defaults
    specified in the image labels.
    """)
)
async def clear_image_resource_limit(
    input: ClearImageResourceLimitInputGQL,
    info: Info[StrawberryGQLContext],
) -> ClearImageResourceLimitResultGQL:
    ctx = info.context

    result = await ctx.processors.image.clear_image_custom_resource_limit_by_id.wait_for_complete(
        ClearImageCustomResourceLimitByIdAction(image_id=ImageID(UUID(input.image_id)))
    )

    return ClearImageResourceLimitResultGQL(image=ImageV2GQL.from_data(result.image_data))


@strawberry.mutation(  # type: ignore[misc]
    description=dedent_strip("""
    Added in 26.2.0.

    Untag an image from its container registry by its ID.

    This removes the image tag from the registry. Only available for HarborV2 registries.
    """)
)
async def untag_image_from_registry(
    input: UntagImageFromRegistryInputGQL,
    info: Info[StrawberryGQLContext],
) -> UntagImageFromRegistryResultGQL:
    ctx = info.context

    result = await ctx.processors.image.untag_image_from_registry.wait_for_complete(
        UntagImageFromRegistryAction(image_id=ImageID(UUID(input.image_id)))
    )

    return UntagImageFromRegistryResultGQL(image=ImageV2GQL.from_data(result.image))


@strawberry.mutation(  # type: ignore[misc]
    description=dedent_strip("""
    Added in 26.2.0.

    Set custom resource limits for an image by its ID.

    This allows overriding the default resource limits specified in the image labels.
    """)
)
async def set_image_resource_limit(
    input: SetImageResourceLimitInputGQL,
    info: Info[StrawberryGQLContext],
) -> SetImageResourceLimitResultGQL:
    ctx = info.context

    resource_limit = ResourceLimitInput(
        slot_name=input.resource_limit.slot_name,
        min_value=Decimal(input.resource_limit.min_value)
        if input.resource_limit.min_value
        else None,
        max_value=Decimal(input.resource_limit.max_value)
        if input.resource_limit.max_value
        else None,
    )

    result = await ctx.processors.image.set_image_resource_limit_by_id.wait_for_complete(
        SetImageResourceLimitByIdAction(
            image_id=ImageID(UUID(input.image_id)),
            resource_limit=resource_limit,
        )
    )

    return SetImageResourceLimitResultGQL(image=ImageV2GQL.from_data(result.image_data))


@strawberry.mutation(  # type: ignore[misc]
    description=dedent_strip("""
    Added in 26.2.0.

    Modify an image's properties by its ID.

    This allows updating various image metadata such as labels, resource limits,
    and supported accelerators.
    """)
)
async def modify_image(
    input: ModifyImageInputGQL,
    info: Info[StrawberryGQLContext],
) -> ModifyImageResultGQL:
    ctx = info.context

    result = await ctx.processors.image.modify_image_by_id.wait_for_complete(
        ModifyImageByIdAction(
            image_id=ImageID(UUID(input.image_id)),
            updater_spec=input.props.to_updater_spec(),
        )
    )

    return ModifyImageResultGQL(image=ImageV2GQL.from_data(result.image))
