import contextvars
import json
from collections.abc import Mapping, Sequence
from typing import Any, NamedTuple

from aiohttp import web
from aiohttp.typedefs import Handler

from .context import RootContext


class AuditLogData(NamedTuple):
    previous: str = json.dumps({})
    current: str = json.dumps({})

    def to_dict(self) -> Mapping[str, str]:
        return {
            "previous": self.previous,
            "current": self.current,
        }


audit_log_data: contextvars.ContextVar[AuditLogData] = contextvars.ContextVar(
    "audit_log_data", default=AuditLogData()
)

audit_log_target: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "audit_log_target", default=None
)


@web.middleware
async def audit_log_middleware(request: web.Request, handler: Handler) -> web.StreamResponse:
    from ai.backend.manager.models import AuditLogRow

    root_ctx: RootContext = request.app["_root.context"]
    success = False
    exc = None

    try:
        res = await handler(request)
        success = True
        return res
    except Exception as e:
        exc = e
        raise
    finally:
        if request.get("audit_log"):
            async with root_ctx.db.begin_session() as sess:
                new_log = AuditLogRow(
                    user_id=request["user"]["uuid"],
                    access_key=request["keypair"]["access_key"],
                    email=request["user"]["email"],
                    action=request["audit_log_action"],
                    data=audit_log_data.get().to_dict(),
                    target_type=request["audit_log_target_type"],
                    success=success,
                    target=audit_log_target.get(),
                    rest_resource=f"{request.method} {request.path}",
                )
                if exc:
                    new_log.error = str(exc)
                sess.add(new_log)


def set_target(target: Any) -> None:
    audit_log_target.set(str(target))


def update_previous(
    data_to_insert: Mapping[str, Any] | Sequence[Any],
) -> None:
    prev_audit_log_data = AuditLogData(
        previous=json.dumps(data_to_insert), current=audit_log_data.get().current
    )
    audit_log_data.set(prev_audit_log_data)


def update_current(
    data_to_insert: Mapping[str, Any] | Sequence[Any],
) -> None:
    prev_audit_log_data = AuditLogData(
        previous=audit_log_data.get().previous, current=json.dumps(data_to_insert)
    )
    audit_log_data.set(prev_audit_log_data)
