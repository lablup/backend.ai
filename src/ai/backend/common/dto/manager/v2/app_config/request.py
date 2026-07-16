"""Request DTOs for the merged app_config v2 read."""

from __future__ import annotations

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.identifier.domain import DomainID

__all__ = (
    "ResolveAppConfigInput",
    "ResolvePublicAppConfigInput",
)


class ResolveAppConfigInput(BaseRequestModel):
    """Input for resolving merged AppConfigs at a named domain, for the acting user.

    ``domain_id`` is the caller's to name; the user is not — the adapter takes it from the
    session, so a resolve is only ever for the acting user.
    """

    config_names: list[str] = Field(
        min_length=1, description="Config names to resolve the merged view for."
    )
    domain_id: DomainID = Field(description="Domain to resolve the domain-scope overlay at.")


class ResolvePublicAppConfigInput(BaseRequestModel):
    """Input for the anonymous, pre-login read, where only public fragments contribute.

    A pre-login screen usually needs several configs at once, so this takes the same batch
    as the authenticated resolve — it just names no principal.
    """

    config_names: list[str] = Field(
        min_length=1, description="Config names to resolve the merged public view for."
    )
