"""Processor package for export operations."""

from __future__ import annotations

from typing import Any

from ai.backend.common.data.entity.keypair import KeyPairFieldType
from ai.backend.manager.actions.registry.field import FieldGroup
from ai.backend.manager.actions.registry.group import ProcessorGroup
from ai.backend.manager.actions.registry.types import FieldGroupMeta
from ai.backend.manager.actions.v2.global_scope.processor import GlobalActionProcessor
from ai.backend.manager.actions.v2.scope.processor import ScopeActionProcessor
from ai.backend.manager.data.audit_log.types import AuditLogData
from ai.backend.manager.data.keypair.types import KeyPairData
from ai.backend.manager.services.export.actions.export_audit_logs_csv import (
    ExportAuditLogsCSVAction,
    ExportAuditLogsCSVActionResult,
)
from ai.backend.manager.services.export.actions.export_keypairs_csv import (
    ExportKeypairsCSVAction,
    ExportKeypairsCSVActionResult,
)
from ai.backend.manager.services.export.actions.export_my_keypairs_csv import (
    ExportMyKeypairsCSVAction,
    ExportMyKeypairsCSVActionResult,
)
from ai.backend.manager.services.export.actions.export_my_sessions_csv import (
    ExportMySessionsCSVAction,
    ExportMySessionsCSVActionResult,
)
from ai.backend.manager.services.export.actions.export_projects_csv import (
    ExportProjectsCSVAction,
    ExportProjectsCSVActionResult,
)
from ai.backend.manager.services.export.actions.export_sessions_by_project_csv import (
    ExportSessionsByProjectCSVAction,
    ExportSessionsByProjectCSVActionResult,
)
from ai.backend.manager.services.export.actions.export_sessions_csv import (
    ExportSessionsCSVAction,
    ExportSessionsCSVActionResult,
)
from ai.backend.manager.services.export.actions.export_users_by_domain_csv import (
    ExportUsersByDomainCSVAction,
    ExportUsersByDomainCSVActionResult,
)
from ai.backend.manager.services.export.actions.export_users_csv import (
    ExportUsersCSVAction,
    ExportUsersCSVActionResult,
)
from ai.backend.manager.services.export.actions.get_report import (
    GetReportAction,
    GetReportActionResult,
)
from ai.backend.manager.services.export.actions.list_reports import (
    ListReportsAction,
    ListReportsActionResult,
)
from ai.backend.manager.services.export.service import ExportService
from ai.backend.manager.services.user.actions.lookup_keypair_owner import (
    LookupBulkKeypairOwnerAction,
    LookupKeypairOwnerAction,
)

__all__ = ("ExportProcessors",)


class ExportProcessors:
    """Export registered reports, authorized against the data each report reads."""

    list_reports: GlobalActionProcessor[ListReportsAction, ListReportsActionResult]
    get_report: GlobalActionProcessor[GetReportAction, GetReportActionResult]
    export_users_csv: GlobalActionProcessor[ExportUsersCSVAction, ExportUsersCSVActionResult]
    export_sessions_csv: GlobalActionProcessor[
        ExportSessionsCSVAction, ExportSessionsCSVActionResult
    ]
    export_projects_csv: GlobalActionProcessor[
        ExportProjectsCSVAction, ExportProjectsCSVActionResult
    ]
    export_keypairs_csv: GlobalActionProcessor[
        ExportKeypairsCSVAction, ExportKeypairsCSVActionResult
    ]
    export_audit_logs_csv: GlobalActionProcessor[
        ExportAuditLogsCSVAction, ExportAuditLogsCSVActionResult
    ]
    export_sessions_by_project_csv: ScopeActionProcessor[
        ExportSessionsByProjectCSVAction, ExportSessionsByProjectCSVActionResult
    ]
    export_users_by_domain_csv: ScopeActionProcessor[
        ExportUsersByDomainCSVAction, ExportUsersByDomainCSVActionResult
    ]
    export_my_sessions_csv: ScopeActionProcessor[
        ExportMySessionsCSVAction, ExportMySessionsCSVActionResult
    ]
    export_my_keypairs_csv: ScopeActionProcessor[
        ExportMyKeypairsCSVAction, ExportMyKeypairsCSVActionResult
    ]

    def __init__(
        self,
        user_group: ProcessorGroup[Any],
        session_group: ProcessorGroup[Any],
        project_group: ProcessorGroup[Any],
        global_group: ProcessorGroup[Any],
        audit_log_group: FieldGroup[AuditLogData],
        service: ExportService,
    ) -> None:
        keypair_group = user_group.field_group(
            FieldGroupMeta(KeyPairFieldType()),
            KeyPairData,
            LookupKeypairOwnerAction,
            LookupBulkKeypairOwnerAction,
        )
        self.list_reports = global_group.global_scope(ListReportsAction, service.list_reports)
        self.get_report = global_group.global_scope(GetReportAction, service.get_report)
        self.export_users_csv = user_group.global_scope(
            ExportUsersCSVAction, service.export_users_csv
        )
        self.export_sessions_csv = session_group.global_scope(
            ExportSessionsCSVAction, service.export_sessions_csv
        )
        self.export_projects_csv = project_group.global_scope(
            ExportProjectsCSVAction, service.export_projects_csv
        )
        self.export_keypairs_csv = keypair_group.global_scope(
            ExportKeypairsCSVAction, service.export_keypairs_csv
        )
        self.export_audit_logs_csv = audit_log_group.global_scope(
            ExportAuditLogsCSVAction, service.export_audit_logs_csv
        )
        self.export_sessions_by_project_csv = session_group.scope(
            ExportSessionsByProjectCSVAction, service.export_sessions_by_project_csv
        )
        self.export_users_by_domain_csv = user_group.scope(
            ExportUsersByDomainCSVAction, service.export_users_by_domain_csv
        )
        self.export_my_sessions_csv = session_group.scope(
            ExportMySessionsCSVAction, service.export_my_sessions_csv
        )
        self.export_my_keypairs_csv = keypair_group.scope(
            ExportMyKeypairsCSVAction, service.export_my_keypairs_csv
        )
