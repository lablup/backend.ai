"""
Federated Image (ImageNode) type with full field definitions for Strawberry GraphQL.
"""

import strawberry
from strawberry.scalars import ID


@strawberry.federation.type(keys=["id"], name="ImageNode", extend=True)
class Image:
    """
    Federated type (ImageNode) with external reference for Strawberry GraphQL.
    """

    id: ID = strawberry.federation.field(external=True)

    @classmethod
    def resolve_reference(cls, id: ID) -> "Image":
        """Resolve an Image reference from Graphene subgraphs."""
        # Return a stub object with just the ID
        # The actual fields will be resolved by the Graphene subgraph
        return cls(id=id)
