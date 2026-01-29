"""
ImageV2 GQL mutations for Strawberry GraphQL.

This module provides GraphQL mutation fields for ImageV2.
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

import strawberry
from strawberry import ID, Info

from ai.backend.common.types import ImageID
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.utils import dedent_strip
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
from ai.backend.manager.services.image.actions.purge_images import (
    PurgeImageByIdAction,
)
from ai.backend.manager.services.image.actions.untag_image_from_registry import (
    UntagImageFromRegistryAction,
)

from .types import ImageV2GQL

# =============================================================================
# Mutation Input Types
# =============================================================================


@strawberry.input(
    description=dedent_strip("""
    Added in 26.2.0.

    Input for forgetting an image by ID.
    """)
)
class ForgetImageInputGQL:
    image_id: ID = strawberry.field(description="The ID of the image to forget.")


@strawberry.input(
    description=dedent_strip("""
    Added in 26.2.0.

    Options for purging an image.
    """)
)
class PurgeImageOptionsGQL:
    remove_from_registry: bool = strawberry.field(
        default=False,
        description="Untag the deleted image from the registry. Only available for HarborV2 registries.",
    )


@strawberry.input(
    description=dedent_strip("""
    Added in 26.2.0.

    Input for purging an image by ID.
    """)
)
class PurgeImageInputGQL:
    image_id: ID = strawberry.field(description="The ID of the image to purge.")
    options: Optional[PurgeImageOptionsGQL] = strawberry.field(
        default=None,
        description="Options for purging the image.",
    )


@strawberry.input(
    description=dedent_strip("""
    Added in 26.2.0.

    Input for creating an alias for an image by ID.
    """)
)
class AliasImageInputGQL:
    image_id: ID = strawberry.field(description="The ID of the image to alias.")
    alias: str = strawberry.field(description="The alias to create.")


@strawberry.input(
    description=dedent_strip("""
    Added in 26.2.0.

    Input for removing an alias from an image.
    """)
)
class DealiasImageInputGQL:
    alias: str = strawberry.field(description="The alias to remove.")


@strawberry.input(
    description=dedent_strip("""
    Added in 26.2.0.

    Input for clearing custom resource limits for an image.
    """)
)
class ClearImageResourceLimitInputGQL:
    image_id: ID = strawberry.field(description="The ID of the image to clear resource limits for.")


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


# =============================================================================
# Mutation Functions
# =============================================================================


@strawberry.mutation(
    description=dedent_strip("""
    Added in 26.2.0.

    Mark an image as deleted by its ID.

    The image is not removed from the database but its status changes to DELETED.
    This is a soft delete operation.

    **Required Role:** SUPERADMIN, ADMIN, or USER
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


@strawberry.mutation(
    description=dedent_strip("""
    Added in 26.2.0.

    Completely purge an image by its ID.

    The image is permanently removed from the database. Optionally, the image
    can also be untagged from the container registry (HarborV2 only).

    **Required Role:** SUPERADMIN, ADMIN, or USER
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


@strawberry.mutation(
    description=dedent_strip("""
    Added in 26.2.0.

    Create an alias for an image by its ID.

    An alias is an alternative name that can be used to reference the image.
    Multiple aliases can be created for the same image.

    **Required Role:** SUPERADMIN
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


@strawberry.mutation(
    description=dedent_strip("""
    Added in 26.2.0.

    Remove an alias from an image.

    **Required Role:** SUPERADMIN
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


@strawberry.mutation(
    description=dedent_strip("""
    Added in 26.2.0.

    Clear custom resource limits for an image by its ID.

    This removes any user-defined resource limits and reverts to the defaults
    specified in the image labels.

    **Required Role:** SUPERADMIN
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
