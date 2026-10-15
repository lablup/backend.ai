"""Request DTOs for bootstrap script v2."""

from __future__ import annotations

from typing import Annotated

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.config.types import MAXIMUM_DOTFILE_SIZE
from ai.backend.common.tristate.unset import UNSET, Unset

__all__ = (
    "CreateBootstrapScriptInput",
    "SearchBootstrapScriptsInput",
    "UpdateBootstrapScriptInput",
)


class CreateBootstrapScriptInput(BaseRequestModel):
    """Input for adding a bootstrap script to the current user. It is not the default."""

    script: str = Field(max_length=MAXIMUM_DOTFILE_SIZE, description="Script text.")


class UpdateBootstrapScriptInput(BaseRequestModel):
    """Input for rewriting the script of a bootstrap script."""

    script: Annotated[str, Field(max_length=MAXIMUM_DOTFILE_SIZE)] | None | Unset = Field(
        default=UNSET, description="New script text. Omit or null to leave unchanged."
    )


class SearchBootstrapScriptsInput(BaseRequestModel):
    """Input for paging through one user's bootstrap scripts, oldest first."""

    first: int | None = Field(
        default=None, ge=1, description="Cursor-based: number of items after cursor"
    )
    after: str | None = Field(default=None, description="Cursor-based: start cursor (exclusive)")
    last: int | None = Field(
        default=None, ge=1, description="Cursor-based: number of items before cursor"
    )
    before: str | None = Field(default=None, description="Cursor-based: end cursor (exclusive)")
    limit: int | None = Field(
        default=None, ge=1, description="Offset-based: maximum number of results."
    )
    offset: int | None = Field(
        default=None, ge=0, description="Offset-based: number of results to skip."
    )
