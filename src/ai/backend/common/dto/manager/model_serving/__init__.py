"""
Common DTOs for model serving (legacy service) system used by both Client SDK and Manager.
"""

from __future__ import annotations

from .request import (
    ListServeRequestModel,
    NewServiceRequestModel,
    ScaleRequestModel,
    SearchServicesRequestModel,
    ServiceConfigModel,
    ServiceFilterModel,
    TokenRequestModel,
    UpdateRouteRequestModel,
)
from .response import (
    CompactServeInfoModel,
    ErrorInfoModel,
    ErrorListResponseModel,
    PaginationInfoModel,
    RouteInfoModel,
    RuntimeInfo,
    RuntimeInfoModel,
    ScaleResponseModel,
    SearchServicesResponseModel,
    ServeInfoModel,
    ServiceSearchItemModel,
    SuccessResponseModel,
    TokenResponseModel,
    TryStartResponseModel,
)

__all__ = (
    # Request models
    "ListServeRequestModel",
    "ServiceFilterModel",
    "SearchServicesRequestModel",
    "ServiceConfigModel",
    "NewServiceRequestModel",
    "ScaleRequestModel",
    "UpdateRouteRequestModel",
    "TokenRequestModel",
    # Response models
    "SuccessResponseModel",
    "CompactServeInfoModel",
    "RouteInfoModel",
    "ServeInfoModel",
    "ServiceSearchItemModel",
    "PaginationInfoModel",
    "SearchServicesResponseModel",
    "TryStartResponseModel",
    "ScaleResponseModel",
    "TokenResponseModel",
    "ErrorInfoModel",
    "ErrorListResponseModel",
    "RuntimeInfo",
    "RuntimeInfoModel",
)
