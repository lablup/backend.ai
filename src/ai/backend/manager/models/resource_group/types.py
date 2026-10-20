from __future__ import annotations

from datetime import timedelta
from typing import Any

from pydantic import ConfigDict, Field, field_serializer

from ai.backend.common.schema.resource_group import PreemptionConfig
from ai.backend.common.types import (
    AgentSelectionStrategy,
    BackendAISchema,
    SessionTypes,
)

__all__ = ("ResourceGroupOpts",)


class ResourceGroupOpts(BackendAISchema):
    model_config = ConfigDict(frozen=True)

    allowed_session_types: list[SessionTypes] = Field(
        default_factory=lambda: [
            SessionTypes.INTERACTIVE,
            SessionTypes.BATCH,
            SessionTypes.INFERENCE,
        ]
    )
    pending_timeout: timedelta = timedelta(seconds=0)
    config: dict[str, Any] = Field(default_factory=dict)

    # Scheduler has a dedicated database column to store its name,
    # but agent selector configuration is stored as a part of the scheduler_opts column.
    agent_selection_strategy: AgentSelectionStrategy = AgentSelectionStrategy.DISPERSED
    agent_selector_config: dict[str, Any] = Field(default_factory=dict)

    enforce_spreading_endpoint_replica: bool = False
    """Deprecated: replaced by the replica group's SessionGroup placement policy (BEP-1064).

    Nothing reads this field — the spreading chain it was meant to drive was
    already dead code (BA-6135). Existing values were migrated onto each
    replica group's SessionGroup (``true`` → ``spread`` + ``preferred``,
    otherwise ``none``). Kept only so persisted ``scheduler_opts`` documents
    keep round-tripping; the column and API drop in the next major.
    """

    allow_fractional_resource_fragmentation: bool = True
    """If set to false, agent will refuse to start kernel when they are forced to fragment fractional resource request"""

    route_cleanup_target_statuses: list[str] = Field(default_factory=lambda: ["unhealthy"])
    """List of route statuses that should be automatically cleaned up. Valid values: healthy, unhealthy, degraded"""

    preemption: PreemptionConfig = Field(default_factory=PreemptionConfig)
    """Preemption configuration"""

    @field_serializer("allowed_session_types", mode="plain")
    def serialize_allowed_session_types(self, value: list[SessionTypes]) -> list[str]:
        return [item.value for item in value]

    @field_serializer("pending_timeout", mode="plain")
    def serialize_pending_timeout(self, value: timedelta) -> float:
        return value.total_seconds()

    @field_serializer("agent_selection_strategy", mode="plain")
    def serialize_agent_selection_strategy(self, value: AgentSelectionStrategy) -> str:
        return value.value
