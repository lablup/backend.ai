"""Scaling group related types."""

from dataclasses import dataclass

from ai.backend.manager.models.scaling_group import ScalingGroupOpts


@dataclass
class ScalingGroupMeta:
    """Scaling group metadata without ORM dependencies."""

    name: str
    scheduler: str
    scheduler_opts: ScalingGroupOpts
