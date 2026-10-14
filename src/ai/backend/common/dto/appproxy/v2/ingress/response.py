from __future__ import annotations

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.dto.appproxy.v2.ingress.types import IngressFrontendKey


class IngressRevisionsResponse(BaseResponseModel):
    revisions: dict[IngressFrontendKey, int] = Field(
        description="Revision held for each frontend key."
    )
