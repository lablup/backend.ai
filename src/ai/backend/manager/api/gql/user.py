import strawberry
from strawberry import ID, Info


@strawberry.federation.type(keys=["id"], name="UserNode", extend=True)
class User:
    id: ID = strawberry.federation.field(external=True)

    @classmethod
    def resolve_reference(cls, id: ID, info: Info) -> "User":
        return cls(id=id)
