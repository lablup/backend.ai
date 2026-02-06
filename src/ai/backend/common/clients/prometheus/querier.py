from abc import ABC, abstractmethod
from dataclasses import dataclass
from uuid import UUID

from ai.backend.common.clients.prometheus.types import ValueType


class MetricQuerier(ABC):
    """Abstract base class for metric queriers.

    A querier is responsible for providing the labels needed for a Prometheus query.
    Different metric types (container, node, etc.) can have different querier implementations.
    """

    @abstractmethod
    def labels(self) -> dict[str, str]:
        """Return the labels to be used in the Prometheus query."""
        ...


@dataclass(kw_only=True)
class ContainerMetricQuerier(MetricQuerier):
    """Querier for container utilization metrics.

    Provides labels for querying container-level metrics from Prometheus.
    """

    metric_name: str
    value_type: ValueType
    kernel_id: UUID | None = None
    session_id: UUID | None = None
    agent_id: str | None = None
    user_id: UUID | None = None
    project_id: UUID | None = None

    def labels(self) -> dict[str, str]:
        """Return the labels for the container metric query."""
        result: dict[str, str] = {
            "container_metric_name": self.metric_name,
            "value_type": self.value_type,
        }
        if self.kernel_id is not None:
            result["kernel_id"] = str(self.kernel_id)
        if self.session_id is not None:
            result["session_id"] = str(self.session_id)
        if self.agent_id is not None:
            result["agent_id"] = self.agent_id
        if self.user_id is not None:
            result["user_id"] = str(self.user_id)
        if self.project_id is not None:
            result["project_id"] = str(self.project_id)
        return result

    def group_by_labels(self) -> tuple[str, ...]:
        """Return the labels to group by in the query.

        Returns labels that are set (not None), plus 'value_type' which is always included.
        """
        result = ["value_type"]

        if self.agent_id is not None:
            result.append("agent_id")
        if self.kernel_id is not None:
            result.append("kernel_id")
        if self.session_id is not None:
            result.append("session_id")
        if self.user_id is not None:
            result.append("user_id")
        if self.project_id is not None:
            result.append("project_id")

        return tuple(result)
