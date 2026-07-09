"""Regression tests for BA-6804.

The per-kernel stream defaultdicts must not accumulate outer keys across the kernel
lifecycle. In particular ``handle_kernel_terminating`` must not auto-vivify a
``stream_stdin_socks`` entry for a kernel that never opened a stream, and it must drop
any existing per-kernel entries on termination.
"""

from __future__ import annotations

import uuid
import weakref
from collections import defaultdict
from types import SimpleNamespace
from typing import cast

from ai.backend.common.types import KernelId
from ai.backend.manager.api.rest.stream.handler import PrivateContext, handle_kernel_terminating
from ai.backend.manager.models.kernel import KernelRow


def _make_app_ctx() -> PrivateContext:
    return cast(
        PrivateContext,
        SimpleNamespace(
            stream_pty_handlers=defaultdict(weakref.WeakSet),
            stream_execute_handlers=defaultdict(weakref.WeakSet),
            stream_proxy_handlers=defaultdict(weakref.WeakSet),
            stream_stdin_socks=defaultdict(weakref.WeakSet),
        ),
    )


def _make_kernel(kernel_id: KernelId) -> KernelRow:
    return cast(KernelRow, SimpleNamespace(id=kernel_id))


class TestHandleKernelTerminating:
    async def test_terminating_kernel_without_streams_adds_no_keys(self) -> None:
        app_ctx = _make_app_ctx()
        kernel = _make_kernel(KernelId(uuid.uuid4()))

        await handle_kernel_terminating(kernel, app_ctx=app_ctx)

        assert len(app_ctx.stream_stdin_socks) == 0
        assert len(app_ctx.stream_pty_handlers) == 0
        assert len(app_ctx.stream_execute_handlers) == 0
        assert len(app_ctx.stream_proxy_handlers) == 0

    async def test_terminating_kernel_removes_existing_keys(self) -> None:
        app_ctx = _make_app_ctx()
        stream_key = KernelId(uuid.uuid4())
        # Simulate streams having been opened for this kernel.
        _ = app_ctx.stream_pty_handlers[stream_key]
        _ = app_ctx.stream_stdin_socks[stream_key]
        kernel = _make_kernel(stream_key)

        await handle_kernel_terminating(kernel, app_ctx=app_ctx)

        assert stream_key not in app_ctx.stream_pty_handlers
        assert stream_key not in app_ctx.stream_execute_handlers
        assert stream_key not in app_ctx.stream_proxy_handlers
        assert stream_key not in app_ctx.stream_stdin_socks
