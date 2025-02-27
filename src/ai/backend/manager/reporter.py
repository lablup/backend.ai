import asyncio
import logging
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import override

import aiotools

from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.models.audit_log import (
    AuditLogEntityType,
    AuditLogOperationType,
    AuditLogRow,
    OperationStatus,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

# TODO: Rename this and add some comments.
REPORT_DONE_MAX_RETRY_CNT = 10


@dataclass
class ReportArgs:
    entity_id: uuid.UUID
    entity_type: AuditLogEntityType
    operation: AuditLogOperationType
    request_id: uuid.UUID
    description: str
    status: OperationStatus = OperationStatus.SUCCESS


@dataclass
class ReportInfo:
    created_at: datetime
    entity_row_id: uuid.UUID


class AbstractReporter(ABC):
    @abstractmethod
    def report_start(self, args: ReportArgs) -> uuid.UUID:
        raise NotImplementedError

    @abstractmethod
    def report_done(self, report_id: uuid.UUID, args: ReportArgs) -> None:
        raise NotImplementedError


class AuditLogReporter(AbstractReporter):
    _db: ExtendedAsyncSAEngine
    _audit_log_task_group: aiotools.PersistentTaskGroup
    _report_infos: dict[uuid.UUID, ReportInfo]

    def __init__(self, db: ExtendedAsyncSAEngine):
        self._db = db
        self._audit_log_task_group = aiotools.PersistentTaskGroup()
        self._report_infos = {}

    @override
    def report_start(
        self,
        args: ReportArgs,
    ) -> uuid.UUID:
        report_id = uuid.uuid4()

        async def _callback() -> None:
            async with self._db.begin_session() as db_session:
                created_at = datetime.now()
                audit_log_row = AuditLogRow(
                    entity_id=args.entity_id,
                    entity_type=AuditLogEntityType.IMAGE,
                    operation=args.operation,
                    duration=timedelta(0),
                    description=args.description,
                    request_id=args.request_id,
                    status=args.status,
                    created_at=created_at,
                )

                db_session.add(audit_log_row)
                await db_session.flush()

                self._report_infos[report_id] = ReportInfo(
                    created_at=created_at,
                    entity_row_id=audit_log_row.id,
                )

        self._audit_log_task_group.create_task(_callback())
        return report_id

    @override
    def report_done(self, report_id: uuid.UUID, args: ReportArgs) -> None:
        async def _callback() -> None:
            retry_cnt = 0
            report_info = self._report_infos.get(report_id)

            while report_info is None:
                if retry_cnt >= REPORT_DONE_MAX_RETRY_CNT:
                    return
                retry_cnt += 1
                await asyncio.sleep(0.1)

            duration = datetime.now() - report_info.created_at
            async with self._db.begin_session() as db_session:
                row_id = report_info.entity_row_id

                audit_log_row = await db_session.get(AuditLogRow, row_id)
                if not audit_log_row:
                    log.error(f"Failed to find audit log row with id {row_id}")
                    return

                audit_log_row.duration = duration
                audit_log_row.status = args.status
                audit_log_row.description = args.description
                # TODO: Handle other fields change

                await db_session.flush()

            del self._report_infos[report_id]

        self._audit_log_task_group.create_task(_callback())

    async def shutdown(self) -> None:
        await self._audit_log_task_group.shutdown()


# TODO: Implement this.
# class SMTPAuditLogReporter(AbstractReporter):
#     @override
#     def report_start(self, args: ReportArgs) -> None:
#         raise NotImplementedError

#     @override
#     def report_done(self, report_id: uuid.UUID, args: ReportArgs) -> None:
#         raise NotImplementedError
