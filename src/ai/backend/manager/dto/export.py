"""Export API request DTOs for path parameters and headers."""

from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel


class ExportPathParam(BaseRequestModel):
    """Path parameter for export endpoints."""

    report_key: str = Field(
        description="The report key to export (e.g., 'sessions', 'users', 'projects')"
    )


class ExportFilenameHeader(BaseRequestModel):
    """Header parameter for optional export filename."""

    filename: str | None = Field(
        default=None,
        validation_alias="X-Export-Filename",
        description="Optional filename for the exported CSV file",
    )


class ExportProjectPathParam(BaseRequestModel):
    """Path parameter for project-scoped export endpoints."""

    project_id: UUID = Field(description="The project ID to scope the export to")


class ExportDomainPathParam(BaseRequestModel):
    """Path parameter for domain-scoped export endpoints."""

    domain_name: str = Field(description="The domain name to scope the export to")
