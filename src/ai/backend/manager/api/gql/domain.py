import strawberry
from strawberry import ID, Info

from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.decorators import BackendAIGQLMeta, gql_federation_type


@gql_federation_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Federation stub for legacy DomainNode.",
    ),
    name="DomainNode",
    keys=["id"],
    extend=True,
)
class Domain:
    id: ID = strawberry.federation.field(external=True)

    @classmethod
    def resolve_reference(cls, id: ID, info: Info) -> "Domain":
        return cls(id=id)


mock_domain_id = ID("UHJvamVjdE5vZGU6ZjM4ZGVhMjMtNTBmYS00MmEwLWI1YWUtMzM4ZjVmNDY5M2Y0")
mock_domain = Domain(id=mock_domain_id)
