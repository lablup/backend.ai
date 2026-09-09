from typing import override

from ai.backend.common.data.entity.types import EntityType

__all__ = ("EtcdConfigEntityType",)


class EtcdConfigEntityType(EntityType):
    @override
    @classmethod
    def name(cls) -> str:
        return "etcd_config"

    @override
    @classmethod
    def description(cls) -> str:
        return "The cluster configuration kept in etcd."
