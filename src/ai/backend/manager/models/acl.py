from __future__ import annotations

from typing import TYPE_CHECKING, Any, Mapping, Sequence

import graphene

from ai.backend.common.types import VFolderHostPermission

if TYPE_CHECKING:
    from .gql import GraphQueryContext


__all__: Sequence[str] = (
    "Permission",
    "get_all_permission",
)


def get_all_permission() -> Mapping[str, Any]:
    return {
        "vfolder_permission_list": [perm.value for perm in VFolderHostPermission],
    }


class Permission(graphene.ObjectType):
    class Meta:
        interfaces: tuple = tuple()

    vfolder_permission_list = graphene.List(lambda: graphene.String)

    @classmethod
    async def load_all(
        cls,
        graph_ctx: GraphQueryContext,
    ) -> Permission:
        return cls(**get_all_permission())
