import strawberry
from strawberry import ID, Info


@strawberry.federation.type(keys=["id"], name="GroupNode", extend=True)
class Project:
    id: ID = strawberry.federation.field(external=True)

    @classmethod
    def resolve_reference(cls, id: ID, info: Info) -> "Project":
        return cls(id=id)


mock_project_id = ID("UHJvamVjdE5vZGU6ZjM4ZGVhMjMtNTBmYS00MmEwLWI1YWUtMzM4ZjVmNDY5M2Y0")
mock_project = Project(id=mock_project_id)
