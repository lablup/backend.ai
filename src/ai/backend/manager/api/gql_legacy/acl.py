from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any

import graphene

from ai.backend.common.types import VFolderHostPermission

if TYPE_CHECKING:
    from .schema import GraphQueryContext

__all__ = ("PredefinedAtomicPermission",)


def get_all_vfolder_host_permissions() -> list[str]:
    return [perm.value for perm in VFolderHostPermission]


def get_all_permissions() -> Mapping[str, Any]:
    return {
        "vfolder_host_permission_list": get_all_vfolder_host_permissions(),
    }


class PredefinedAtomicPermission(graphene.ObjectType):
    vfolder_host_permission_list = graphene.List(lambda: graphene.String)

    async def resolve_vfolder_host_permission_list(self, info: graphene.ResolveInfo) -> list[str]:
        return get_all_vfolder_host_permissions()

    @classmethod
    async def load_all(
        cls,
        graph_ctx: GraphQueryContext,
    ) -> PredefinedAtomicPermission:
        return cls(**get_all_permissions())
