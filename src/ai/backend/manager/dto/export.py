"""Export API request DTOs for path parameters and headers."""

from typing import Optional

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel


class ExportPathParam(BaseRequestModel):
    """Path parameter for export endpoints."""

    report_key: str = Field(
        description="The report key to export (e.g., 'sessions', 'users', 'projects')"
    )


class ExportFilenameHeader(BaseRequestModel):
    """Header parameter for optional export filename."""

    filename: Optional[str] = Field(
        default=None,
        validation_alias="X-Export-Filename",
        description="Optional filename for the exported CSV file",
    )
