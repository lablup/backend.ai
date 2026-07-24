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

    # TODO(BA-7003): domain_ids is a list but only the first element is used. This is a
    # temporary, strictly-incorrect shape kept for wire compatibility; collapse it to a
    # single domain once BA-7003 lands.
    domain_ids: list[DomainID] = Field(
        min_length=1,
        description="Domains to resolve the domain-scope overlay at. Only the first is used.",
    )


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
