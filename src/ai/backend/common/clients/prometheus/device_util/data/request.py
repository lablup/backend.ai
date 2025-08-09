from dataclasses import dataclass
from typing import Optional

from ...data.request import QueryRange


@dataclass
class DeviceUtilizationQueryParameter:
    value_type: Optional[str]
    device_metric_name: Optional[str] = None
    agent_id: Optional[str] = None
    device_id: Optional[str] = None

    range: Optional[QueryRange] = None
