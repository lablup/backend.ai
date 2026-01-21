import strawberry
from strawberry import ID, Info


@strawberry.federation.type(keys=["id"], name="ComputeSessionNode", extend=True)
class Session:
    id: ID = strawberry.federation.field(external=True)

    @classmethod
    def resolve_reference(cls, id: ID, info: Info) -> "Session":
        return cls(id=id)
