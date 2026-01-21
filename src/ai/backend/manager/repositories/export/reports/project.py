"""Project (group) export report definition."""

from __future__ import annotations

import json

from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.repositories.base.export import (
    ExportFieldDef,
    ExportFieldType,
    ReportDef,
)

# Field definitions for project export
PROJECT_FIELDS: list[ExportFieldDef] = [
    ExportFieldDef(
        key="id",
        name="ID",
        description="Project UUID",
        field_type=ExportFieldType.UUID,
        column=GroupRow.id,
    ),
    ExportFieldDef(
        key="name",
        name="Name",
        description="Project name",
        field_type=ExportFieldType.STRING,
        column=GroupRow.name,
    ),
    ExportFieldDef(
        key="description",
        name="Description",
        description="Project description",
        field_type=ExportFieldType.STRING,
        column=GroupRow.description,
    ),
    ExportFieldDef(
        key="domain_name",
        name="Domain",
        description="Domain name",
        field_type=ExportFieldType.STRING,
        column=GroupRow.domain_name,
    ),
    ExportFieldDef(
        key="is_active",
        name="Active",
        description="Active status",
        field_type=ExportFieldType.BOOLEAN,
        column=GroupRow.is_active,
    ),
    ExportFieldDef(
        key="total_resource_slots",
        name="Resource Slots",
        description="Total resource slots allocated",
        field_type=ExportFieldType.JSON,
        column=GroupRow.total_resource_slots,
        formatter=lambda v: json.dumps(dict(v)) if v else "",
    ),
    ExportFieldDef(
        key="created_at",
        name="Created At",
        description="Creation time",
        field_type=ExportFieldType.DATETIME,
        column=GroupRow.created_at,
        formatter=lambda v: v.isoformat() if v else "",
    ),
    ExportFieldDef(
        key="modified_at",
        name="Modified At",
        description="Last modification time",
        field_type=ExportFieldType.DATETIME,
        column=GroupRow.modified_at,
        formatter=lambda v: v.isoformat() if v else "",
    ),
]


# Report definition
PROJECT_REPORT = ReportDef(
    report_key="projects",
    name="Projects",
    description="Project (group) export report",
    select_from=GroupRow.__table__,
    fields=PROJECT_FIELDS,
)
