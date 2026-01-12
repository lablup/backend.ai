"""Session export report definition."""

from __future__ import annotations

import json

from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.repositories.base.export import (
    ExportFieldDef,
    ExportFieldType,
    ReportDef,
)

# Field definitions for session export
SESSION_FIELDS: list[ExportFieldDef] = [
    ExportFieldDef(
        key="id",
        name="ID",
        description="Session UUID",
        field_type=ExportFieldType.UUID,
        column=SessionRow.id,
    ),
    ExportFieldDef(
        key="name",
        name="Name",
        description="Session name",
        field_type=ExportFieldType.STRING,
        column=SessionRow.name,
    ),
    ExportFieldDef(
        key="session_type",
        name="Type",
        description="Session type",
        field_type=ExportFieldType.ENUM,
        column=SessionRow.session_type,
        formatter=lambda v: str(v) if v else "",
    ),
    ExportFieldDef(
        key="domain_name",
        name="Domain",
        description="Domain name",
        field_type=ExportFieldType.STRING,
        column=SessionRow.domain_name,
    ),
    ExportFieldDef(
        key="access_key",
        name="Access Key",
        description="Owning access key",
        field_type=ExportFieldType.STRING,
        column=SessionRow.access_key,
    ),
    ExportFieldDef(
        key="status",
        name="Status",
        description="Session status",
        field_type=ExportFieldType.ENUM,
        column=SessionRow.status,
        formatter=lambda v: str(v) if v else "",
    ),
    ExportFieldDef(
        key="status_info",
        name="Status Info",
        description="Status details",
        field_type=ExportFieldType.STRING,
        column=SessionRow.status_info,
    ),
    ExportFieldDef(
        key="scaling_group_name",
        name="Scaling Group",
        description="Scaling group name",
        field_type=ExportFieldType.STRING,
        column=SessionRow.scaling_group_name,
    ),
    ExportFieldDef(
        key="cluster_size",
        name="Cluster Size",
        description="Number of cluster nodes",
        field_type=ExportFieldType.INTEGER,
        column=SessionRow.cluster_size,
    ),
    ExportFieldDef(
        key="occupying_slots",
        name="Resources",
        description="Occupied resource slots",
        field_type=ExportFieldType.JSON,
        column=SessionRow.occupying_slots,
        formatter=lambda v: json.dumps(dict(v), default=str) if v else "",
    ),
    ExportFieldDef(
        key="created_at",
        name="Created At",
        description="Session creation time",
        field_type=ExportFieldType.DATETIME,
        column=SessionRow.created_at,
        formatter=lambda v: v.isoformat() if v else "",
    ),
    ExportFieldDef(
        key="terminated_at",
        name="Terminated At",
        description="Session termination time",
        field_type=ExportFieldType.DATETIME,
        column=SessionRow.terminated_at,
        formatter=lambda v: v.isoformat() if v else "",
    ),
]


# Report definition
SESSION_REPORT = ReportDef(
    report_key="sessions",
    name="Sessions",
    description="Compute session export report",
    select_from=SessionRow.__table__,
    fields=SESSION_FIELDS,
)
