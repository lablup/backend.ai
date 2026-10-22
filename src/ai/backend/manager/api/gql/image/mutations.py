from uuid import UUID

from strawberry import UNSET
from strawberry.scalars import JSON

from ai.backend.common.dto.manager.v2.common import PartialBulkPayload
from ai.backend.common.dto.manager.v2.image.request import (
    PartialBulkDeleteImagesInput,
    PartialBulkRestoreImagesInput,
    PartialBulkUpdateImageItemInput,
    PartialBulkUpdateImagesInput,
    ScanImageInput,
    UpdateImageBody,
)
from ai.backend.common.dto.manager.v2.image.response import (
    DeleteImagePayload,
    ImageNode,
    RestoreImagePayload,
    ScanImagePayload,
    UpdateImagePayload,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.common_types import PartialBulkFailureGQL
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_field,
    gql_pydantic_input,
    gql_pydantic_type,
)
from ai.backend.manager.api.gql.image.types import ImageV2GQL
from ai.backend.manager.api.gql.pydantic_compat import PydanticInputMixin, PydanticOutputMixin


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Input for scanning one image tag and selecting its architecture.",
    ),
    name="ScanImageInput",
)
class ScanImageInputGQL(PydanticInputMixin[ScanImageInput]):
    canonical: str = gql_field(
        description="Image canonical name to scan. Defaults to latest when the tag is omitted."
    )
    architecture: str = gql_field(description="Image architecture to return.")


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Fields to update on an image. All fields optional.",
    ),
    name="UpdateImageInput",
)
class UpdateImageInputGQL(PydanticInputMixin[UpdateImageBody]):
    name: str | None = gql_field(default=UNSET, description="Updated canonical name.")
    registry: str | None = gql_field(default=UNSET, description="Updated registry hostname.")
    image: str | None = gql_field(
        default=UNSET, description="Updated namespace/path within registry."
    )
    tag: str | None = gql_field(default=UNSET, description="Updated image tag.")
    architecture: str | None = gql_field(default=UNSET, description="Updated CPU architecture.")
    is_local: bool | None = gql_field(default=UNSET, description="Updated local-only status.")
    size_bytes: int | None = gql_field(default=UNSET, description="Updated image size in bytes.")
    type: str | None = gql_field(
        default=UNSET, description="Updated image type (compute, system, service)."
    )
    config_digest: str | None = gql_field(default=UNSET, description="Updated config digest.")
    labels: JSON | None = gql_field(default=UNSET, description="Updated labels dict.")
    supported_accelerators: str | None = gql_field(
        default=UNSET, description="Updated accelerator string. Null clears."
    )
    resource_limits: JSON | None = gql_field(
        default=UNSET, description="Updated resource limits dict."
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="One image of a partial bulk update and the fields to update on it.",
    ),
    name="PartialBulkUpdateImageItemInput",
)
class PartialBulkUpdateImageItemInputGQL(PydanticInputMixin[PartialBulkUpdateImageItemInput]):
    id: UUID = gql_field(description="ID of the image to update.")
    input: UpdateImageInputGQL = gql_field(description="Fields to update on the image.")


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Input for updating several images, each answered for separately.",
    ),
    name="PartialBulkUpdateImagesInput",
)
class PartialBulkUpdateImagesInputGQL(PydanticInputMixin[PartialBulkUpdateImagesInput]):
    items: list[PartialBulkUpdateImageItemInputGQL] = gql_field(
        description="The images to update, each with its fields."
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Input for forgetting several images, each answered for separately.",
    ),
    name="PartialBulkDeleteImagesInput",
)
class PartialBulkDeleteImagesInputGQL(PydanticInputMixin[PartialBulkDeleteImagesInput]):
    ids: list[UUID] = gql_field(description="IDs of the images to forget.")


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Input for restoring several forgotten images, each answered for separately.",
    ),
    name="PartialBulkRestoreImagesInput",
)
class PartialBulkRestoreImagesInputGQL(PydanticInputMixin[PartialBulkRestoreImagesInput]):
    ids: list[UUID] = gql_field(description="IDs of the images to restore.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Scanned image matching the requested architecture.",
    ),
    model=ScanImagePayload,
    name="ScanImagePayload",
)
class ScanImagePayloadGQL(PydanticOutputMixin[ScanImagePayload]):
    item: ImageV2GQL = gql_field(description="Scanned image matching the requested architecture.")


@gql_pydantic_type(
    BackendAIGQLMeta(added_version=NEXT_RELEASE_VERSION, description="Updated image."),
    model=UpdateImagePayload,
    name="UpdateImagePayload",
)
class UpdateImagePayloadGQL(PydanticOutputMixin[UpdateImagePayload]):
    item: ImageV2GQL = gql_field(description="Updated image.")


@gql_pydantic_type(
    BackendAIGQLMeta(added_version=NEXT_RELEASE_VERSION, description="Forgotten image."),
    model=DeleteImagePayload,
    name="DeleteImagePayload",
)
class DeleteImagePayloadGQL(PydanticOutputMixin[DeleteImagePayload]):
    item: ImageV2GQL = gql_field(description="Forgotten image.")


@gql_pydantic_type(
    BackendAIGQLMeta(added_version=NEXT_RELEASE_VERSION, description="Restored image."),
    model=RestoreImagePayload,
    name="RestoreImagePayload",
)
class RestoreImagePayloadGQL(PydanticOutputMixin[RestoreImagePayload]):
    item: ImageV2GQL = gql_field(description="Restored image.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Result of a partial bulk image operation: the images processed and the ones "
            "that failed."
        ),
    ),
    model=PartialBulkPayload[ImageNode],
    name="PartialBulkImagesPayload",
)
class PartialBulkImagesPayloadGQL(PydanticOutputMixin[PartialBulkPayload[ImageNode]]):
    """Payload for partial bulk image mutations."""

    successes: list[ImageV2GQL] = gql_field(description="The images processed, as they now stand.")
    failed: list[PartialBulkFailureGQL] = gql_field(
        description="The images not processed, each with the reason."
    )
