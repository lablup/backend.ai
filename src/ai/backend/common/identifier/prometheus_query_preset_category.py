from typing import NewType
from uuid import UUID

__all__ = ("PrometheusQueryPresetCategoryID",)


PrometheusQueryPresetCategoryID = NewType("PrometheusQueryPresetCategoryID", UUID)
