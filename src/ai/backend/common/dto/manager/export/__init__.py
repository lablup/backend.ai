"""
Common DTOs for export system used by both Client SDK and Manager.

This package provides DTOs for the CSV export API:
- Common types: OrderDirection, ExportFieldInfo, ExportReportInfo
- Common request types: DateTimeRangeFilter
- Report-specific DTOs: Users, Sessions, Projects, AuditLogs
- Response DTOs: ListExportReportsResponse, GetExportReportResponse
"""

from __future__ import annotations

from ai.backend.common.dto.manager.query import DateTimeRangeFilter

from .audit_logs import (
    AuditLogExportCSVRequest,
    AuditLogExportFilter,
    AuditLogExportOrder,
    AuditLogExportOrderField,
)
from .keypairs import KeypairExportCSVRequest
from .projects import (
    BooleanFilter,
    ProjectExportCSVRequest,
    ProjectExportFilter,
    ProjectExportOrder,
    ProjectExportOrderField,
)
from .response import (
    GetExportReportResponse,
    ListExportReportsResponse,
)
from .sessions import (
    SessionExportCSVRequest,
    SessionExportFilter,
    SessionExportOrder,
    SessionExportOrderField,
)
from .types import (
    ExportFieldInfo,
    ExportReportInfo,
    ExportReportKey,
    OrderDirection,
)
from .users import (
    UserExportCSVRequest,
    UserExportFilter,
    UserExportOrder,
    UserExportOrderField,
)

__all__ = (
    # Common Types
    "OrderDirection",
    "ExportFieldInfo",
    "ExportReportInfo",
    "ExportReportKey",
    # Common Request DTOs
    "DateTimeRangeFilter",
    "BooleanFilter",
    # User Export DTOs
    "UserExportFilter",
    "UserExportOrder",
    "UserExportOrderField",
    "UserExportCSVRequest",
    # Session Export DTOs
    "SessionExportFilter",
    "SessionExportOrder",
    "SessionExportOrderField",
    "SessionExportCSVRequest",
    # Project Export DTOs
    "ProjectExportFilter",
    "ProjectExportOrder",
    "ProjectExportOrderField",
    "ProjectExportCSVRequest",
    # Keypair Export DTOs
    "KeypairExportCSVRequest",
    # Audit Log Export DTOs
    "AuditLogExportFilter",
    "AuditLogExportOrder",
    "AuditLogExportOrderField",
    "AuditLogExportCSVRequest",
    # Response DTOs
    "GetExportReportResponse",
    "ListExportReportsResponse",
)
