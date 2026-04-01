"""
Federated Image (ImageNode) type with full field definitions for Strawberry GraphQL.
"""

import strawberry
from strawberry.scalars import ID

from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.decorators import BackendAIGQLMeta, gql_federation_type


@gql_federation_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Federation stub for legacy ImageNode.",
    ),
    name="ImageNode",
    keys=["id"],
    extend=True,
)
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
