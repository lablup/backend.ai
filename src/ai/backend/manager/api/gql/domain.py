import strawberry
from strawberry import ID, Info


@strawberry.federation.type(keys=["id"], name="DomainNode", extend=True)
class Domain:
    id: ID = strawberry.federation.field(external=True)

    @classmethod
    def resolve_reference(cls, id: ID, info: Info) -> "Domain":
        return cls(id=id)


mock_domain_id = ID("UHJvamVjdE5vZGU6ZjM4ZGVhMjMtNTBmYS00MmEwLWI1YWUtMzM4ZjVmNDY5M2Y0")
mock_domain = Domain(id=mock_domain_id)
