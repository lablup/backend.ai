from enum import Enum, StrEnum
from functools import lru_cache


class EndpointStatus(StrEnum):
    READY = "READY"
    PROVISIONING = "PROVISIONING"
    HEALTHY = "HEALTHY"
    UNHEALTHY = "UNHEALTHY"
    DESTROYING = "DESTROYING"
    DESTROYED = "DESTROYED"
    DEGRADED = "DEGRADED"


class EndpointLifecycle(Enum):
    PENDING = "pending"
    CREATED = "created"  # Deprecated, use READY instead
    SCALING = "scaling"
    READY = "ready"
    DESTROYING = "destroying"
    DESTROYED = "destroyed"

    @classmethod
    @lru_cache(maxsize=1)
    def active_states(cls) -> set["EndpointLifecycle"]:
        return {cls.PENDING, cls.CREATED, cls.SCALING, cls.READY}

    @classmethod
    @lru_cache(maxsize=1)
    def need_scaling_states(cls) -> set["EndpointLifecycle"]:
        return {cls.CREATED, cls.READY}

    @classmethod
    @lru_cache(maxsize=1)
    def inactive_states(cls) -> set["EndpointLifecycle"]:
        return {cls.DESTROYING, cls.DESTROYED}
