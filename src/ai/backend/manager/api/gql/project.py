import strawberry
from strawberry import ID, Info


@strawberry.federation.type(keys=["id"], name="GroupNode", extend=True)
class Project:
    id: ID = strawberry.federation.field(external=True)

    @classmethod
    def resolve_reference(cls, id: ID, info: Info) -> "Project":
        return cls(id=id)
