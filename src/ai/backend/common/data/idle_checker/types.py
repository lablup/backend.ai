from __future__ import annotations

import enum
from typing import Self

from pydantic import Field, model_validator

from ai.backend.common.types import BackendAISchema, SessionTypes


class CheckerType(enum.StrEnum):
    """Discriminator for the kind of idle checker; selects the concrete spec."""

    SESSION_LIFETIME = "session_lifetime"
    NETWORK_TIMEOUT = "network_timeout"
    UTILIZATION = "utilization"


class SessionLifetimeSpec(BackendAISchema):
    """Config for ``CheckerType.SESSION_LIFETIME``.

    Concrete fields (e.g. max lifetime) land with the checker-logic stories.
    """


class NetworkTimeoutSpec(BackendAISchema):
    """Config for ``CheckerType.NETWORK_TIMEOUT``.

    Concrete fields land with the checker-logic stories.
    """


class UtilizationSpec(BackendAISchema):
    """Config for ``CheckerType.UTILIZATION``.

    Concrete fields land with the checker-logic stories.
    """


class IdleCheckerSpec(BackendAISchema):
    """Config payload stored in ``idle_checkers.spec`` as a single JSONB document.

    ``type`` selects which sub-config is valid; exactly one sub-config field must
    be present for the chosen type (validated below). Stored via ``PydanticColumn``.
    """

    type: CheckerType = Field(description="Idle checker kind; selects the sub-config.")
    target_session_types: frozenset[SessionTypes] = Field(
        default=frozenset({SessionTypes.INTERACTIVE, SessionTypes.BATCH}),
        description="Session types this checker applies to; other types are skipped.",
    )
    session_lifetime: SessionLifetimeSpec | None = Field(
        default=None, description="session_lifetime config."
    )
    network: NetworkTimeoutSpec | None = Field(default=None, description="network_timeout config.")
    utilization: UtilizationSpec | None = Field(default=None, description="utilization config.")

    @model_validator(mode="after")
    def validate_spec_matches_type(self) -> Self:
        match self.type:
            case CheckerType.SESSION_LIFETIME:
                if self.session_lifetime is None:
                    raise ValueError("session_lifetime is required for type=session_lifetime.")
                if self.network or self.utilization:
                    raise ValueError("Only session_lifetime is allowed for type=session_lifetime.")
            case CheckerType.NETWORK_TIMEOUT:
                if self.network is None:
                    raise ValueError("network is required for type=network_timeout.")
                if self.session_lifetime or self.utilization:
                    raise ValueError("Only network is allowed for type=network_timeout.")
            case CheckerType.UTILIZATION:
                if self.utilization is None:
                    raise ValueError("utilization is required for type=utilization.")
                if self.session_lifetime or self.network:
                    raise ValueError("Only utilization is allowed for type=utilization.")
        return self
