from typing import NewType
from uuid import UUID

__all__ = ("PrometheusQueryPresetID",)


PrometheusQueryPresetID = NewType("PrometheusQueryPresetID", UUID)
