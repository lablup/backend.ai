from __future__ import annotations

from typing import TYPE_CHECKING, Any, List, Mapping, Sequence

import graphene

from ai.backend.common.types import VFolderHostPermission

if TYPE_CHECKING:
    from .gql import GraphQueryContext


__all__: Sequence[str] = (
    "VFolderAtomicPermission",
    "get_all_permissions",
)


def get_all_vfolder_permissions() -> List[str]:
    return [perm.value for perm in VFolderHostPermission]


def get_all_permissions() -> Mapping[str, Any]:
    return {
        "vfolder_permission_list": get_all_vfolder_permissions(),
    }


class VFolderAtomicPermission(graphene.ObjectType):
    vfolder_permission_list = graphene.List(lambda: graphene.String)

    async def resolve_vfolder_permission_list(self, info: graphene.ResolveInfo) -> List[str]:
        return get_all_vfolder_permissions()

    @classmethod
    async def load_all(
        cls,
        graph_ctx: GraphQueryContext,
    ) -> VFolderAtomicPermission:
        return cls(**get_all_permissions())
