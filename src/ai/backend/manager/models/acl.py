from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, List, Sequence

import graphene

from ai.backend.common.types import VFolderHostPermission

if TYPE_CHECKING:
    from .gql import GraphQueryContext


__all__: Sequence[str] = (
    "PredefinedAtomicPermission",
    "get_all_permissions",
)


def get_all_vfolder_host_permissions() -> List[str]:
    return [perm.value for perm in VFolderHostPermission]


def get_all_permissions() -> Mapping[str, Any]:
    return {
        "vfolder_host_permission_list": get_all_vfolder_host_permissions(),
    }


class PredefinedAtomicPermission(graphene.ObjectType):
    vfolder_host_permission_list = graphene.List(lambda: graphene.String)

    async def resolve_vfolder_host_permission_list(self, info: graphene.ResolveInfo) -> List[str]:
        return get_all_vfolder_host_permissions()

    @classmethod
    async def load_all(
        cls,
        graph_ctx: GraphQueryContext,
    ) -> PredefinedAtomicPermission:
        return cls(**get_all_permissions())
