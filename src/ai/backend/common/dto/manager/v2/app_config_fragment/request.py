"""Request DTOs for app_config_fragment v2."""

from __future__ import annotations

from typing import Any, Self
from uuid import UUID

from pydantic import Field, model_validator

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.data.app_config.types import AppConfigScopeType

__all__ = (
    "AppConfigFragmentUpdateItem",
    "BulkPurgeAppConfigFragmentInput",
    "BulkUpdateAppConfigFragmentInput",
    "CreateAppConfigFragmentInput",
    "UpdateAppConfigFragmentInput",
)


class CreateAppConfigFragmentInput(BaseRequestModel):
    """Input for creating a new app config fragment at a given scope."""

    config_name: str = Field(
        min_length=1,
        max_length=128,
        description="Registered config name (FK to app_config_definitions).",
    )
    scope_type: AppConfigScopeType = Field(
        description="Scope the fragment is written at (public | domain | user)."
    )
    scope_id: UUID | None = Field(
        default=None,
        description="Scope identifier: the domain id (domain scope) or the user id (user scope). "
        "Null for public scope, which has no owner.",
    )
    config: dict[str, Any] = Field(description="The fragment's JSON config document.")

    @model_validator(mode="after")
    def _check_scope_id(self) -> Self:
        if self.scope_type is AppConfigScopeType.PUBLIC:
            if self.scope_id is not None:
                raise ValueError("scope_id must be null for public scope.")
        elif self.scope_id is None:
            raise ValueError("scope_id is required for domain and user scopes.")
        return self


class UpdateAppConfigFragmentInput(BaseRequestModel):
    """Input for updating one app config fragment's config document.

    The target fragment is identified by the request path, not by this body.
    """

    config: dict[str, Any] = Field(description="The replacement JSON config document.")


class AppConfigFragmentUpdateItem(BaseRequestModel):
    """One item of a bulk update, carrying its own target id.

    Bulk requests address many fragments in a single call, so the id belongs in the body
    here — unlike the single-fragment :class:`UpdateAppConfigFragmentInput`.
    """

    id: UUID = Field(description="App config fragment id to update.")
    config: dict[str, Any] = Field(description="The replacement JSON config document.")


class BulkUpdateAppConfigFragmentInput(BaseRequestModel):
    """Input for updating many fragments' config documents (per-item partial success)."""

    items: list[AppConfigFragmentUpdateItem] = Field(
        min_length=1, description="Fragments to update, each identified by its id."
    )


class BulkPurgeAppConfigFragmentInput(BaseRequestModel):
    """Input for purging many fragments (per-item partial success)."""

    ids: list[UUID] = Field(min_length=1, description="Fragment ids to purge.")
