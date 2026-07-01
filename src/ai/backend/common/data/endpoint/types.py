from enum import Enum, StrEnum
from functools import lru_cache
from typing import Any, Self


class EndpointStatus(StrEnum):
    READY = "READY"
    PROVISIONING = "PROVISIONING"
    HEALTHY = "HEALTHY"
    UNHEALTHY = "UNHEALTHY"
    DESTROYING = "DESTROYING"
    DESTROYED = "DESTROYED"
    DEGRADED = "DEGRADED"


class EndpointLifecycle(Enum):
    """Endpoint lifecycle phase.

    Active phases flow PENDING → DEPLOYING → READY → DESTROYING → DESTROYED.
    Scaling (replica count adjustment) is tracked on the separate
    ``ScalingState`` dimension so the lifecycle itself stays monotonic;
    ``SCALING`` / ``CREATED`` remain defined only for wire-level
    compatibility with historical rows and are never written by new code.
    """

    PENDING = "pending"
    CREATED = "created"
    """Deprecated (use READY). Retained for legacy-row deserialisation;
    never produced by current code paths."""
    SCALING = "scaling"
    """Deprecated (use ``ScalingState.SCALING`` with ``lifecycle=READY``).
    Retained for legacy-row deserialisation; never produced by current
    code paths."""
    READY = "ready"
    DEPLOYING = "deploying"
    DESTROYING = "destroying"
    DESTROYED = "destroyed"

    @classmethod
    @lru_cache(maxsize=1)
    def active_states(cls) -> set["EndpointLifecycle"]:
        # CREATED / SCALING remain in this set for one release window so
        # legacy rows written before the scaling_state split are not
        # filtered out before the data migration in S2 runs. They become
        # unreachable after the migration and can be dropped here in a
        # follow-up PR.
        return {cls.PENDING, cls.CREATED, cls.SCALING, cls.READY, cls.DEPLOYING}

    @classmethod
    @lru_cache(maxsize=1)
    def need_scaling_states(cls) -> set["EndpointLifecycle"]:
        # Transitional: pre-split rows with lifecycle=CREATED are
        # indistinguishable from READY for auto-scaling purposes. Keeps
        # those rows eligible until the S2 data migration rewrites them
        # to READY; drop CREATED here afterwards.
        return {cls.CREATED, cls.READY}

    @classmethod
    @lru_cache(maxsize=1)
    def inactive_states(cls) -> set["EndpointLifecycle"]:
        return {cls.DESTROYING, cls.DESTROYED}

    @classmethod
    def _missing_(cls, value: Any) -> Self | None:
        # Accept v2 :class:`ModelDeploymentStatus` aliases on the wire so
        # historical / future callers that hand us the new naming still
        # resolve to a valid lifecycle value.
        if isinstance(value, str):
            alias = _DEPLOYMENT_STATUS_TO_LIFECYCLE_ALIASES.get(value.lower())
            if alias is not None:
                return cls(alias)
        return None


# Map v2 :class:`ModelDeploymentStatus` values back onto the lowercase
# :class:`EndpointLifecycle` form. Used by ``EndpointLifecycle._missing_``.
_DEPLOYMENT_STATUS_TO_LIFECYCLE_ALIASES: dict[str, str] = {
    "stopping": "destroying",
    "stopped": "destroyed",
}


class ScalingState(StrEnum):
    """Whether an endpoint is currently adjusting its replica count.

    Orthogonal to :class:`EndpointLifecycle`: a healthy ``READY`` endpoint
    may also be ``SCALING`` while the coordinator reconciles
    ``desired_replica_count`` against the actual replica set. Scaling only
    happens once ``current_revision_id`` is set — the check is enforced by
    the handler gate, not by this enum.
    """

    STABLE = "stable"
    SCALING = "scaling"
