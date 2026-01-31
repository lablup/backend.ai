"""
Request DTOs for Keypair export report.

This module defines the request structure specific to keypair data export.
Note: Keypair export currently does not support filtering or ordering.
"""

from __future__ import annotations

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel

__all__ = ("KeypairExportCSVRequest",)


class KeypairExportCSVRequest(BaseRequestModel):
    """
    Request body for keypair CSV export operations.

    This is the request model for POST /export/keypairs/csv endpoint.
    Note: Filtering and ordering are not yet supported for keypair exports.
    """

    fields: list[str] | None = Field(
        default=None,
        description=(
            "List of field keys to include in the export. "
            "Available basic fields: access_key, user_id, user_uuid, is_active, is_admin, "
            "created_at, modified_at, last_used, resource_policy_name. "
            "Available JOIN fields: user_*, resource_policy_*, resource_group_*, session_*. "
            "If not specified or empty, all available fields will be exported."
        ),
    )
    encoding: str = Field(
        default="utf-8",
        description=(
            "Character encoding for the CSV output. "
            "Supported values: 'utf-8' (default, recommended for most uses), "
            "'euc-kr' (for Korean systems requiring legacy encoding)."
        ),
    )
