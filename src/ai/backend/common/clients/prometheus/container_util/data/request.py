from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from ...data.request import QueryRange


@dataclass
class ContainerUtilizationQueryParameter:
    value_type: Optional[str]
    container_metric_name: Optional[str] = None
    agent_id: Optional[str] = None
    kernel_id: Optional[UUID] = None
    session_id: Optional[UUID] = None
    user_id: Optional[UUID] = None
    project_id: Optional[UUID] = None

    range: Optional[QueryRange] = None
