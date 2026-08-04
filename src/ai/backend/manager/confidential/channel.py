from __future__ import annotations

import asyncio
import logging
import uuid
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any, Final, override

import sqlalchemy as sa

from ai.backend.common.dto.agent.response import CodeCompletionResp
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.kernel_runner import (
    AbstractCodeRunner,
    ChannelEndpoint,
    ChannelNotEstablished,
    FramedTransport,
    NextResult,
    RunnerTransport,
    StaleAnswerRefused,
    default_api_version,
    default_client_features,
)
from ai.backend.common.types import KernelId, SessionId
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.models.confidential.row import ConfidentialChannelRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))

REDIAL_ATTEMPTS: Final = 3


class ChannelCodeRunner(AbstractCodeRunner):
    def __init__(
        self,
        kernel_id: KernelId,
        session_id: SessionId,
        event_producer: EventProducer,
        *,
        endpoint: ChannelEndpoint,
        client_features: frozenset[str] | None = None,
    ) -> None:
        super().__init__(
            kernel_id, session_id, event_producer, exec_timeout=0, client_features=client_features
        )
        self._endpoint = endpoint
        self._framed = FramedTransport(endpoint)

    @property
    def epoch(self) -> int:
        return self._framed.epoch

    @override
    async def _create_transport(self) -> RunnerTransport:
        return self._framed


class ConfidentialChannel:
    def __init__(self, db: ExtendedAsyncSAEngine, event_producer: EventProducer) -> None:
        self._db = db
        self._event_producer = event_producer
        self._runners: dict[KernelId, ChannelCodeRunner] = {}
        self._lock = asyncio.Lock()

    async def vouch(self, kernel_id: KernelId) -> ConfidentialChannelRow:
        async with self._db.begin_readonly_session() as db_session:
            row = await db_session.get(ConfidentialChannelRow, uuid.UUID(str(kernel_id)))
        if row is None:
            raise ChannelNotEstablished(
                extra_msg=f"kernel {kernel_id} was never given a session channel key"
            )
        if row.expires_at <= datetime.now(UTC):
            raise ChannelNotEstablished(
                extra_msg=f"the channel identity of kernel {kernel_id} expired at {row.expires_at}"
            )
        return row

    async def rebind(self, kernel_id: KernelId, fingerprint: str, token: str) -> None:
        async with self._db.begin_session() as db_session:
            await db_session.execute(
                sa.update(ConfidentialChannelRow)
                .where(ConfidentialChannelRow.kernel_id == uuid.UUID(str(kernel_id)))
                .values(fingerprint=fingerprint, token=token)
            )
        await self.release(kernel_id)

    async def runner(self, kernel_id: KernelId) -> ChannelCodeRunner:
        async with self._lock:
            existing = self._runners.get(kernel_id)
            if existing is not None:
                return existing
            row = await self.vouch(kernel_id)
            host, _, port = row.relay_addr.rpartition(":")
            runner = await ChannelCodeRunner.new(
                kernel_id,
                SessionId(row.session_id),
                self._event_producer,
                endpoint=ChannelEndpoint(
                    relay_host=host,
                    relay_port=int(port),
                    kernel_id=str(kernel_id),
                    guest_port=row.channel_port,
                    certificate_fingerprint=row.fingerprint,
                    token=row.token,
                ),
                client_features=default_client_features,
            )
            self._runners[kernel_id] = runner
            return runner

    async def release(self, kernel_id: KernelId) -> None:
        async with self._lock:
            runner = self._runners.pop(kernel_id, None)
        if runner is not None:
            await runner.close()

    async def _dialled(self, kernel_id: KernelId, verb: Any) -> Any:
        last: Exception | None = None
        for _ in range(REDIAL_ATTEMPTS):
            runner = await self.runner(kernel_id)
            try:
                answer = await verb(runner)
            except ChannelNotEstablished as e:
                last = e
                await self.release(kernel_id)
                continue
            await self._record_epoch(kernel_id, runner.epoch)
            return answer
        raise last if last is not None else ChannelNotEstablished(extra_msg=str(kernel_id))

    async def _record_epoch(self, kernel_id: KernelId, epoch: int) -> None:
        if epoch < 0:
            return
        async with self._db.begin_session() as db_session:
            await db_session.execute(
                sa.update(ConfidentialChannelRow)
                .where(
                    (ConfidentialChannelRow.kernel_id == uuid.UUID(str(kernel_id)))
                    & (ConfidentialChannelRow.epoch < epoch)
                )
                .values(epoch=epoch)
            )

    async def execute(
        self,
        kernel_id: KernelId,
        run_id: str | None,
        mode: str,
        text: str,
        *,
        opts: Mapping[str, Any],
        api_version: int = default_api_version,
        flush_timeout: float = 2.0,
    ) -> NextResult:
        async def run(runner: ChannelCodeRunner) -> NextResult:
            await runner.attach_output_queue(run_id)
            match mode:
                case "query":
                    await runner.feed_code(text)
                case "input":
                    await runner.feed_input(text)
                case "batch":
                    await runner.feed_batch(opts)
                case "continue":
                    pass
                case _:
                    raise StaleAnswerRefused(extra_msg=f"unknown execution mode {mode!r}")
            return await runner.get_next_result(api_ver=api_version, flush_timeout=flush_timeout)

        return await self._dialled(kernel_id, run)

    async def check_status(self, kernel_id: KernelId) -> dict[str, float]:
        status = await self._dialled(kernel_id, lambda r: r.feed_and_get_status())
        if not status:
            raise StaleAnswerRefused(
                extra_msg=f"kernel {kernel_id} answered its status verb with nothing"
            )
        return status

    async def interrupt(self, kernel_id: KernelId) -> dict[str, Any]:
        await self._dialled(kernel_id, lambda r: r.feed_interrupt())
        return {"status": "finished"}

    async def get_completions(
        self, kernel_id: KernelId, text: str, opts: Mapping[str, Any]
    ) -> CodeCompletionResp:
        return CodeCompletionResp(
            result=await self._dialled(kernel_id, lambda r: r.feed_and_get_completion(text, opts))
        )

    async def start_service(
        self, kernel_id: KernelId, service: Mapping[str, Any]
    ) -> dict[str, Any]:
        return await self._dialled(kernel_id, lambda r: r.feed_start_service(service))

    async def start_model_service(
        self, kernel_id: KernelId, model_service: Mapping[str, Any]
    ) -> dict[str, Any]:
        return await self._dialled(kernel_id, lambda r: r.feed_start_model_service(model_service))

    async def shutdown_service(self, kernel_id: KernelId, service: str) -> None:
        await self._dialled(kernel_id, lambda r: r.feed_shutdown_service(service))

    async def get_service_apps(self, kernel_id: KernelId) -> dict[str, Any]:
        return await self._dialled(kernel_id, lambda r: r.feed_service_apps())

    async def notify_event(self, kernel_id: KernelId, evdata: Any) -> None:
        await self._dialled(kernel_id, lambda r: r.feed_event(evdata))

    async def list_files(self, kernel_id: KernelId, path: str) -> dict[str, Any]:
        return await self._dialled(kernel_id, lambda r: r.feed_list_files(path))

    async def upload_file(self, kernel_id: KernelId, path: str, filedata: bytes) -> None:
        await self._dialled(kernel_id, lambda r: r.feed_upload_file(path, filedata))

    async def download_file(self, kernel_id: KernelId, path: str) -> bytes:
        return await self._dialled(kernel_id, lambda r: r.feed_download_file(path))

    async def download_single(self, kernel_id: KernelId, path: str) -> bytes:
        return await self._dialled(kernel_id, lambda r: r.feed_download_single(path))

    async def get_logs(self, kernel_id: KernelId) -> dict[str, Any]:
        return await self._dialled(kernel_id, lambda r: r.feed_get_logs())

    async def close(self) -> None:
        for kernel_id in list(self._runners):
            await self.release(kernel_id)
