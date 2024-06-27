import contextvars
import json
import uuid
from typing import Any, Mapping, Sequence

from aiohttp import web
from aiohttp.typedefs import Handler

from .context import RootContext

audit_log_data: contextvars.ContextVar[dict[str, Any]] = contextvars.ContextVar(
    "audit_log_data", default={"before": {}, "after": {}}
)

audit_log_target: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "audit_log_target", default=None
)


@web.middleware
async def audit_log_middleware(request: web.Request, handler: Handler) -> web.StreamResponse:
    from ai.backend.manager.models import AuditLogRow

    root_ctx: RootContext = request.app["_root.context"]
    handler_attr = getattr(handler, "_backend_attrs", {})
    success = False

    try:
        res = await handler(request)
        success = True
        return res
    except Exception:
        raise
    finally:
        if request.get("audit_log_applicable"):
            async with root_ctx.db.begin_session() as sess:
                new_log = AuditLogRow(
                    uuid.uuid4(),
                    request["user"]["uuid"],
                    request["keypair"]["access_key"],
                    request["user"]["email"],
                    handler_attr["audit_log_action"],
                    audit_log_data.get(),
                    handler_attr["audit_log_target_type"],
                    success,
                    target=audit_log_target.get(),
                    rest_resource=f"{request.method} {request.path}",
                )
                sess.add(new_log)


def set_target(target: Any) -> None:
    audit_log_target.set(str(target))


def update_after_data(
    data_to_insert: Mapping[str, Any] | Sequence[Any],
) -> None:
    prev_audit_log_data = audit_log_data.get().copy()
    prev_audit_log_data["after"] = json.dumps(data_to_insert)
    audit_log_data.set(prev_audit_log_data)


def update_before_data(
    data_to_insert: Mapping[str, Any] | Sequence[Any],
) -> None:
    prev_audit_log_data = audit_log_data.get().copy()
    prev_audit_log_data["before"] = json.dumps(data_to_insert)
    audit_log_data.set(prev_audit_log_data)
