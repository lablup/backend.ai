"""
Federated types that reference existing GraphQL entities.
These types connect the new Strawberry schema with the existing Graphene schema.
"""

import strawberry
from strawberry import ID


@strawberry.federation.type(name="UserNode", keys=["id"], extend=True)
class User:
    id: ID = strawberry.federation.field(external=True)

    @classmethod
    def resolve_reference(cls, id: ID):
        return cls(id=id)


@strawberry.federation.type(name="ScalingGroupNode", keys=["id"], extend=True)
class ResourceGroup:
    id: ID = strawberry.federation.field(external=True)

    @classmethod
    def resolve_reference(cls, id: ID):
        return cls(id=id)


@strawberry.federation.type(name="EndpointToken", keys=["token"], extend=True)
class AccessToken:
    token: str = strawberry.federation.field(external=True)

    @classmethod
    def resolve_reference(cls, token: str) -> "AccessToken":
        return cls(token=token)


@strawberry.federation.type(name="VirtualFolderNode", keys=["id"], extend=True)
class VFolder:
    id: ID = strawberry.federation.field(external=True)

    @classmethod
    def resolve_reference(cls, id: ID) -> "VFolder":
        return cls(id=id)


@strawberry.federation.type(name="EndpointAutoScalingRuleNode", keys=["id"], extend=True)
class AutoScalingRule:
    id: ID = strawberry.federation.field(external=True)

    @classmethod
    def resolve_reference(cls, id: ID) -> "AutoScalingRule":
        return cls(id=id)


@strawberry.federation.type(name="ImageNode", keys=["id"], extend=True)
class Image:
    id: ID = strawberry.federation.field(external=True)

    @classmethod
    def resolve_reference(cls, id: ID) -> "Image":
        return cls(id=id)
