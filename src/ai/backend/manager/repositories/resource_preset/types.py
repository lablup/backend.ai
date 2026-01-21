"""Type definitions for resource preset repository."""

from __future__ import annotations

from dataclasses import dataclass

from ai.backend.common.json import dump_json, load_json
from ai.backend.common.types import ResourceSlot

from .db_source.types import PerScalingGroupResourceData, PresetAllocatabilityData


@dataclass
class CheckPresetsResult:
    """Result of checking resource presets from repository."""

    presets: list[PresetAllocatabilityData]
    keypair_limits: ResourceSlot
    keypair_using: ResourceSlot
    keypair_remaining: ResourceSlot
    group_limits: ResourceSlot
    group_using: ResourceSlot
    group_remaining: ResourceSlot
    scaling_group_remaining: ResourceSlot
    scaling_groups: dict[str, PerScalingGroupResourceData]

    def to_cache(self) -> bytes:
        """
        Serialize the result to a JSON string for caching.

        :return: JSON bytes representation of the result
        """
        cache_data = {
            "presets": [p.to_cache() for p in self.presets],
            "keypair_limits": self.keypair_limits.to_json(),
            "keypair_using": self.keypair_using.to_json(),
            "keypair_remaining": self.keypair_remaining.to_json(),
            "group_limits": self.group_limits.to_json(),
            "group_using": self.group_using.to_json(),
            "group_remaining": self.group_remaining.to_json(),
            "scaling_group_remaining": self.scaling_group_remaining.to_json(),
            "scaling_groups": {
                sgname: sg_data.to_cache() for sgname, sg_data in self.scaling_groups.items()
            },
        }

        return dump_json(cache_data)

    @classmethod
    def from_cache(cls, cached_data: bytes) -> CheckPresetsResult:
        """
        Deserialize the result from a cached JSON string.

        :param cached_data: JSON bytes from cache
        :return: CheckPresetsResult instance
        """
        data = load_json(cached_data)

        return cls(
            presets=[PresetAllocatabilityData.from_cache(p) for p in data["presets"]],
            keypair_limits=ResourceSlot.from_json(data["keypair_limits"]),
            keypair_using=ResourceSlot.from_json(data["keypair_using"]),
            keypair_remaining=ResourceSlot.from_json(data["keypair_remaining"]),
            group_limits=ResourceSlot.from_json(data["group_limits"]),
            group_using=ResourceSlot.from_json(data["group_using"]),
            group_remaining=ResourceSlot.from_json(data["group_remaining"]),
            scaling_group_remaining=ResourceSlot.from_json(data["scaling_group_remaining"]),
            scaling_groups={
                sgname: PerScalingGroupResourceData.from_cache(sg_data)
                for sgname, sg_data in data["scaling_groups"].items()
            },
        )
