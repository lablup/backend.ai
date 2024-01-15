import contextvars
import logging
from datetime import datetime
from typing import Any, Iterable, Mapping

import sqlalchemy as sa
from aiohttp import web
from aiohttp.typedefs import Handler
from pydantic.v1.utils import deep_update

from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.manager.api.context import RootContext
from ai.backend.manager.models.audit_logs import audit_logs

__all__ = (
    "audit_log_middleware",
    "update_audit_log_target",
    "update_after_data",
    "update_before_data",
    "empty_after_data",
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]

audit_log_data: contextvars.ContextVar[dict[str, Any]] = contextvars.ContextVar(
    "audit_log_data", default={"before": {}, "after": {}}
)

audit_log_target: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "audit_log_target", default=None
)


@web.middleware
async def audit_log_middleware(request: web.Request, handler: Handler) -> web.StreamResponse:
    root_ctx: RootContext = request.app["_root.context"]
    user_info = extract_user_info(request)
    handler_attr = getattr(handler, "_backend_attrs", {})
    audit_log_applicable = handler_attr.get("audit_log_applicable", False)

    try:
        res = await handler(request)
        success = True
        return res
    except Exception:
        success = False
        raise
    finally:
        if audit_log_applicable:
            await record_audit_log(
                user_info,
                handler_attr,
                request,
                success,
                root_ctx,
            )


def extract_user_info(request: web.Request) -> dict[str, str]:
    return {
        "user_id": str(request["user"]["uuid"]),
        "access_key": request["keypair"]["access_key"],
        "email": request["user"]["email"],
    }


async def record_audit_log(
    user_info: dict[str, str],
    handler_attr: dict[str, Any],
    request: web.Request,
    success: bool,
    root_ctx: RootContext,
):
    data = {
        "user_id": user_info["user_id"],
        "access_key": user_info["access_key"],
        "email": user_info["email"],
        "action": handler_attr.get("audit_log_action"),
        "data": audit_log_data.get(),
        "target_type": handler_attr.get("audit_log_target_type"),
        "target": audit_log_target.get(),
        "created_at": datetime.utcnow(),
        "success": success,
        "rest_api_path": f"{request.method} {request.path}",
    }

    try:
        log.info("AUDIT_LOG: {}", data)
        async with root_ctx.db.begin_session() as session:
            query = sa.insert(audit_logs, data)
            await session.execute(query)
    except Exception as e:
        log.error("Failed to write audit log: {}", e)


def update_audit_log_target(target: Any) -> None:
    audit_log_target.set(target)


def updated_data(target_data: dict[str, Any], values_to_update: dict[str, Any]) -> dict[str, Any]:
    current_audit_log_data = target_data.copy()
    return deep_update(current_audit_log_data, values_to_update)


def update_audit_log_data_by_field_name(field_to_update: str, value: Any) -> None:
    audit_log_data.set(
        updated_data(
            target_data=audit_log_data.get(),
            values_to_update={
                field_to_update: value,
            },
        )
    )


def update_after_data(data_to_insert: dict[str, Any] | Iterable[dict[str, Any]]) -> None:
    update_audit_log_data_by_field_name("after", data_to_insert)


def update_before_data(data_to_insert: dict[str, Any] | Iterable[dict[str, Any]]) -> None:
    update_audit_log_data_by_field_name("before", data_to_insert)


def empty_after_data() -> None:
    current_audit_log_data = audit_log_data.get().copy()
    current_audit_log_data["after"] = {}
    audit_log_data.set(current_audit_log_data)


def stringify_entry_values(entry: Mapping[str, Any]) -> dict[str, str]:
    return {k: str(v) for k, v in dict(entry).items()}
