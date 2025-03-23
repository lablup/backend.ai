import graphene


class MetircResultValue(graphene.ObjectType):
    class Meta:
        description = "Added in 25.5.0. A pair of timestamp and value."

    timestamp = graphene.Float()
    value = graphene.String()
