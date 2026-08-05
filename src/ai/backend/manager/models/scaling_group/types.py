from __future__ import annotations

from datetime import timedelta
from decimal import Decimal
from typing import Any

from pydantic import ConfigDict, Field, field_serializer, field_validator

from ai.backend.common.types import BackendAISchema, ResourceSlot

__all__ = ("ConfidentialScalingGroupOpts", "FairShareScalingGroupSpec")

CAPABILITY_DISCLOSURE = (
    "Confidential capability is operator-declared and backed by the signed broker provisioning"
    " record named here. It is an integrity claim about our own paperwork, not a cryptographic"
    " one: the key broker protocol offers no way to attest a running broker."
)

METADATA_EGRESS_DISCLOSURE = (
    "Metadata egress is not a scaling-group setting and takes no session launch flag. The agent"
    " rejects traffic from the guest bridge to the metadata endpoint and the management networks"
    " named in its own configuration, which no tenant input reaches, and a launch option naming a"
    " metadata endpoint is refused rather than accepted and ignored."
)

NONCE_RESIDUAL_DISCLOSURE = (
    "The launch nonce binds a session with a claim quota equal to its member count. It preserves"
    " cross-session isolation and does not provide member-against-member isolation within a"
    " session; the quota binds count rather than identity, so a host that suppresses a legitimate"
    " member can take the freed slot with a measurement-identical guest, whereupon the suppressed"
    " member's fetch is refused and its session dies loudly."
)


class ConfidentialScalingGroupOpts(BackendAISchema):
    model_config = ConfigDict(frozen=True)

    enabled: bool = False
    broker_endpoint: str = ""
    broker_admin_token: str = ""
    shim_public_addr: str = ""
    provisioning_record: str = ""
    pipeline_public_key: str = ""
    attested_identity: str = ""
    insecure_development: bool = False
    tcb_grace_period: timedelta = timedelta(days=7)
    admission_limit_per_image: int = 1
    folder_key_escrow_path: str = ""
    folder_key_escrow_key: str = ""
    channel_relay_port: int = 6021
    channel_guest_port: int = 2010
    tunnel_port_range: tuple[int, int] = (51821, 51899)

    @property
    def confidential_capable(self) -> bool:
        return self.enabled and not self.insecure_development

    @field_serializer("tcb_grace_period", mode="plain")
    def serialize_tcb_grace_period(self, value: timedelta) -> float:
        return value.total_seconds()


class FairShareScalingGroupSpec(BackendAISchema):
    """Fair Share calculation configuration for a Resource Group.

    Used for Fair Share metric calculation regardless of the scheduler type.
    """

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    half_life_days: int = 7
    """Half-life for exponential decay in days."""

    lookback_days: int = 28
    """Total lookback period in days for usage aggregation."""

    decay_unit_days: int = 1
    """Granularity of decay buckets in days."""

    default_weight: Decimal = Decimal("1.0")
    """Default weight for entities without explicit weight in this scaling group."""

    resource_weights: ResourceSlot = Field(default_factory=ResourceSlot)
    """Weights for each resource type when calculating normalized usage.

    If a resource type is not specified, default weight (1.0) is used.
    Example: ResourceSlot({"cpu": 1.0, "mem": 0.001, "cuda.device": 10.0})
    """

    @field_serializer("resource_weights", mode="plain")
    def serialize_resource_weights(self, value: ResourceSlot) -> dict[str, Any]:
        """Serialize ResourceSlot to dict for JSON compatibility."""
        return {k: str(v) for k, v in value.items()}

    @field_validator("resource_weights", mode="before")
    @classmethod
    def validate_resource_weights(cls, value: Any) -> ResourceSlot:
        """Deserialize dict to ResourceSlot.

        Converts string values to Decimal to avoid BinarySize parsing issues.
        """
        if isinstance(value, ResourceSlot):
            return value
        if isinstance(value, dict):
            # Convert string values to Decimal to bypass BinarySize parsing
            converted = {k: Decimal(v) if isinstance(v, str) else v for k, v in value.items()}
            return ResourceSlot(converted)
        return ResourceSlot()
