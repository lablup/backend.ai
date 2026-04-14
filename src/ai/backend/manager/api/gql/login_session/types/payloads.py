"""LoginSession GraphQL mutation payload types."""

from __future__ import annotations

from ai.backend.common.dto.manager.v2.login_session.response import (
    RevokeLoginSessionPayload as RevokeLoginSessionPayloadDTO,
)
from ai.backend.common.dto.manager.v2.login_session.response import (
    UnblockUserPayload as UnblockUserPayloadDTO,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_pydantic_type,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticOutputMixin


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Payload returned after revoking a login session.",
    ),
    model=RevokeLoginSessionPayloadDTO,
    all_fields=True,
    name="RevokeLoginSessionPayload",
)
class RevokeLoginSessionPayloadGQL(PydanticOutputMixin[RevokeLoginSessionPayloadDTO]):
    pass


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Payload returned after clearing a user's failed-login block.",
    ),
    model=UnblockUserPayloadDTO,
    all_fields=True,
    name="UnblockUserPayload",
)
class UnblockUserPayloadGQL(PydanticOutputMixin[UnblockUserPayloadDTO]):
    pass
