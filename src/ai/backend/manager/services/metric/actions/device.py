from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseAction, BaseActionResult

from ..types import DeviceMetricOptionalLabel, DeviceMetricResult


@dataclass
class DeviceMetricMetadataAction(BaseAction):
    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def entity_type(cls) -> str:
        return "agent_metric_metadata"

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "query"


@dataclass
class DeviceMetricMetadataActionResult(BaseActionResult):
    metric_names: list[str]

    @override
    def entity_id(self) -> Optional[str]:
        return None


@dataclass
class DeviceMetricAction(BaseAction):
    metric_name: str
    labels: DeviceMetricOptionalLabel

    start: str
    end: str
    step: str

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def entity_type(cls) -> str:
        return "container_metric"

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "query"


@dataclass
class DeviceMetricActionResult(BaseActionResult):
    result: list[DeviceMetricResult]

    @override
    def entity_id(self) -> Optional[str]:
        return None


@dataclass
class DeviceCurrentMetricAction(BaseAction):
    labels: DeviceMetricOptionalLabel

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def entity_type(cls) -> str:
        return "device_current_metric"

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "query"


@dataclass
class DeviceCurrentMetricActionResult(BaseActionResult):
    result: list[DeviceMetricResult]

    @override
    def entity_id(self) -> Optional[str]:
        return None
