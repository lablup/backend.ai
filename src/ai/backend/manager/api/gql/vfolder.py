import strawberry
from strawberry import ID, Info

from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_federation_type,
)


@gql_federation_type(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Federation stub for legacy VirtualFolderNode.",
    ),
    name="VirtualFolderNode",
    keys=["id"],
    extend=True,
)
class VFolder:
    id: ID = strawberry.federation.field(external=True)

    @classmethod
    def resolve_reference(cls, id: ID, info: Info) -> "VFolder":
        return cls(id=id)
