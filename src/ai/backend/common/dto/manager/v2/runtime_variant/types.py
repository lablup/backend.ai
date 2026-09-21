from __future__ import annotations

from enum import StrEnum
from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel


class RuntimeVariantOrderField(StrEnum):
    NAME = "name"
    CREATED_AT = "created_at"


class RuntimeVariantUsedBy(BaseRequestModel):
    """Entities whose use narrows the runtime variants read; every id is AND-ed.

    An entity the caller cannot read refuses the request.
    """

    deployment: list[UUID] | None = Field(
        default=None, description="Deployments whose revisions name the runtime variant"
    )
