from ai.backend.common.dto.manager.v2.image.request import ScanImageInput
from ai.backend.common.dto.manager.v2.image.response import ScanImagePayload
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
        description="Input for scanning one image tag and selecting its architecture.",
    ),
    name="ScanImageInput",
)
class ScanImageInputGQL(PydanticInputMixin[ScanImageInput]):
    canonical: str = gql_field(
        description="Image canonical name to scan. Defaults to latest when the tag is omitted."
    )
    architecture: str = gql_field(description="Image architecture to return.")


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
