"""Request DTOs for the merged app_config v2 read."""

from __future__ import annotations

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.identifier.domain import DomainID

__all__ = (
    "AppConfigScopeArgumentsDTO",
    "ResolveAppConfigInput",
    "ResolvePublicAppConfigInput",
)


class AppConfigScopeArgumentsDTO(BaseRequestModel):
    """The scope a caller supplies for a resolve — the domain, never the user.

    The wire twin of the repository's ``AppConfigScopeArguments``: the adapter fills the
    user from the session, so a resolve is only ever for the acting user. Grow new
    caller-supplied scope dimensions here, mirroring the repository type, rather than adding
    flat fields to the request.
    """

    domain_id: DomainID = Field(description="Domain to resolve the domain-scope overlay at.")


class ResolveAppConfigInput(BaseRequestModel):
    """Input for resolving merged AppConfigs at a named scope, for the acting user."""

    config_names: list[str] = Field(
        min_length=1, description="Config names to resolve the merged view for."
    )
    scope_arguments: AppConfigScopeArgumentsDTO = Field(
        description="Caller-supplied scope for the resolve."
    )


class ResolvePublicAppConfigInput(BaseRequestModel):
    """Input for the anonymous, pre-login read, where only public fragments contribute.

    A pre-login screen usually needs several configs at once, so this takes the same batch
    as the authenticated resolve — it just names no principal.
    """

    config_names: list[str] = Field(
        min_length=1, description="Config names to resolve the merged public view for."
    )
