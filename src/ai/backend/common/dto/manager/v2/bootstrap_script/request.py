from __future__ import annotations

from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.data.entity.bootstrap_script import BootstrapScriptID
from ai.backend.common.dto.manager.config.types import MAXIMUM_DOTFILE_SIZE
from ai.backend.common.dto.manager.query import (
    DateTimeFilter,
    UUIDFilter,
)
from ai.backend.common.dto.manager.v2.bootstrap_script.types import (
    BootstrapScriptOrderField,
    BootstrapScriptScope,
)
from ai.backend.common.dto.manager.v2.common import OrderDirection


class CreateBootstrapScriptInput(BaseRequestModel):
    """Add a bootstrap script to a user. The script is not the user's default."""

    user_id: UUID = Field(description="ID of the user the script is set on.")
    script: str = Field(
        max_length=MAXIMUM_DOTFILE_SIZE, description="Content of the first revision."
    )


class AddBootstrapScriptRevisionInput(BaseRequestModel):
    """Replace the content of a bootstrap script with a new revision."""

    id: BootstrapScriptID = Field(description="ID of the script.")
    script: str = Field(max_length=MAXIMUM_DOTFILE_SIZE, description="Content of the revision.")


class SwitchDefaultBootstrapScriptInput(BaseRequestModel):
    """Make a script the default of the user it is set on."""

    user_id: UUID = Field(description="ID of the user the script is set on.")
    id: BootstrapScriptID = Field(description="ID of the script.")


class PurgeBootstrapScriptInput(BaseRequestModel):
    """Remove a script that is not the default."""

    id: BootstrapScriptID = Field(description="ID of the script.")


class BootstrapScriptFilter(BaseRequestModel):
    """Filter for bootstrap scripts."""

    field_id: UUIDFilter | None = Field(default=None, description="Filter by script ID.")
    is_default: bool | None = Field(
        default=None, description="Filter by whether the script is the user's default."
    )
    created_at: DateTimeFilter | None = Field(default=None, description="Filter by creation time.")

    AND: list[BootstrapScriptFilter] | None = Field(
        default=None, description="AND logical combinator."
    )
    OR: list[BootstrapScriptFilter] | None = Field(
        default=None, description="OR logical combinator."
    )
    NOT: list[BootstrapScriptFilter] | None = Field(
        default=None, description="NOT logical combinator."
    )


BootstrapScriptFilter.model_rebuild()


class BootstrapScriptOrder(BaseRequestModel):
    """Order specification for bootstrap scripts."""

    field: BootstrapScriptOrderField = Field(description="Field to order by.")
    direction: OrderDirection = Field(default=OrderDirection.ASC, description="Order direction.")


class ScopedSearchBootstrapScriptsInput(BaseRequestModel):
    """Input for searching the bootstrap scripts of the named users."""

    scope: BootstrapScriptScope = Field(description="Scope (OR across all items).")
    filter: BootstrapScriptFilter | None = Field(default=None, description="Filter conditions.")
    order: list[BootstrapScriptOrder] | None = Field(
        default=None, description="Order specifications."
    )
    first: int | None = Field(default=None, description="Cursor pagination: number of items.")
    after: str | None = Field(default=None, description="Cursor pagination: after cursor.")
    last: int | None = Field(default=None, description="Cursor pagination: last N items.")
    before: str | None = Field(default=None, description="Cursor pagination: before cursor.")
    limit: int | None = Field(default=None, description="Offset pagination: maximum items.")
    offset: int | None = Field(default=None, description="Offset pagination: number to skip.")
