from ai.backend.common.dto.manager.v2.image.request import RescanImagesInput
from ai.backend.common.dto.manager.v2.image.response import RescanImagesPayload
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
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
        description="Input for rescanning one image tag and selecting its architecture.",
    ),
    name="RescanImagesInput",
)
class RescanImagesInputGQL(PydanticInputMixin[RescanImagesInput]):
    canonical: str = gql_field(
        description="Image canonical name to rescan. Defaults to latest when the tag is omitted."
    )
    architecture: str = gql_field(description="Image architecture to return.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Rescanned image matching the requested architecture.",
    ),
    model=RescanImagesPayload,
    name="RescanImagesPayload",
)
class RescanImagesPayloadGQL(PydanticOutputMixin[RescanImagesPayload]):
    item: ImageV2GQL = gql_field(description="Rescanned image matching the requested architecture.")
