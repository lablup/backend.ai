import strawberry
from strawberry import ID, Info

from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.decorators import BackendAIGQLMeta, gql_federation_type


@gql_federation_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Federation stub for legacy UserNode.",
    ),
    name="UserNode",
    keys=["id"],
    extend=True,
)
class User:
    id: ID = strawberry.federation.field(external=True)

    @classmethod
    def resolve_reference(cls, id: ID, info: Info) -> "User":
        return cls(id=id)
