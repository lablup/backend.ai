import strawberry


@strawberry.federation.type(keys=["id"], name="ScalingGroupNode", extend=True)
class ResourceGroup:
    """
    Federated ResourceGroup (ScalingGroup) type with external reference for Strawberry GraphQL.
    """

    id: strawberry.ID = strawberry.federation.field(external=True)

    @classmethod
    def resolve_reference(cls, id: strawberry.ID) -> "ResourceGroup":
        """Resolve a ResourceGroup reference from Graphene subgraphs."""
        # Return a stub object with just the ID
        # The actual fields will be resolved by the Graphene subgraph
        return cls(id=id)
