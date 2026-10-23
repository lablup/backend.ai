"""Request DTOs for system session environ DTO v2."""

from __future__ import annotations

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.project import ProjectID

__all__ = ("AdminResolveSystemSessionEnvironInput",)


class AdminResolveSystemSessionEnvironInput(BaseRequestModel):
    """Input for reading the system session environ a session in a domain and project receives."""

    domain_id: DomainID = Field(description="The domain the session belongs to.")
    project_id: ProjectID = Field(description="The project the session belongs to.")
