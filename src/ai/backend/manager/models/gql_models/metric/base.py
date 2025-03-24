from decimal import Decimal
from typing import Optional

import graphene


class MetircResultValue(graphene.ObjectType):
    class Meta:
        description = "Added in 25.5.0. A pair of timestamp and value."

    timestamp = graphene.Float()
    value = graphene.String()


class ContainerUtilizationMetric(graphene.ObjectType):
    class Meta:
        description = "Added in 25.5.0."

    metric_name = graphene.String()
    value_type = graphene.String(description="One of 'current', 'capacity', 'pct'.")
    values = graphene.List(MetircResultValue)

    max_value = graphene.String(
        description="The maximum value of the metric in given time range. null if no data."
    )
    avg_value = graphene.String(
        description="The average value of the metric in given time range. null if no data."
    )

    async def resolve_max_value(self, info: graphene.ResolveInfo) -> Optional[str]:
        if not self.values:
            return None
        return max(self.values, key=lambda x: Decimal(x.value)).value

    async def resolve_avg_value(self, info: graphene.ResolveInfo) -> Optional[str]:
        if not self.values:
            return None
        avg_val = sum(Decimal(x.value) for x in self.values) / len(self.values)
        return str(avg_val)
