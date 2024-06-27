import contextvars
import json
import uuid
from typing import Any, Mapping, Sequence

from aiohttp import web
from aiohttp.typedefs import Handler

from .context import RootContext

audit_log_data: contextvars.ContextVar[dict[str, Any]] = contextvars.ContextVar(
    "audit_log_data", default={"previous": {}, "current": {}}
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
                    uuid.uuid4(),
                    request["user"]["uuid"],
                    request["keypair"]["access_key"],
                    request["user"]["email"],
                    request["audit_log_action"],
                    audit_log_data.get(),
                    request["audit_log_target_type"],
                    success,
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
    prev_audit_log_data = audit_log_data.get().copy()
    prev_audit_log_data["previous"] = json.dumps(data_to_insert)
    audit_log_data.set(prev_audit_log_data)


def update_current(
    data_to_insert: Mapping[str, Any] | Sequence[Any],
) -> None:
    prev_audit_log_data = audit_log_data.get().copy()
    prev_audit_log_data["current"] = json.dumps(data_to_insert)
    audit_log_data.set(prev_audit_log_data)
