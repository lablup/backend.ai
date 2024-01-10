import contextvars
import logging
from datetime import datetime
from typing import Any, Mapping

import sqlalchemy as sa
from aiohttp import web
from aiohttp.typedefs import Handler
from pydantic.v1.utils import deep_update

from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.manager.api.context import RootContext
from ai.backend.manager.models.audit_logs import audit_logs

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]

audit_log_data: contextvars.ContextVar[dict[str, Any]] = contextvars.ContextVar(
    "audit_log_data", default={}
)


@web.middleware
async def audit_log_middleware(request: web.Request, handler: Handler) -> web.StreamResponse:
    # TODO: in near future we can change this condition to dict so we can add more conditions

    if request.method == "GET":
        return await handler(request)

    root_ctx: RootContext = request.app["_root.context"]
    user_uuid = str(request["user"]["uuid"])
    access_key = request["keypair"]["access_key"]
    user_email = request["user"]["email"]

    audit_log_data.set({
        "user_id": user_uuid,
        "access_key": access_key,
        "email": user_email,
        "action": None,
        "data": {"before": {}, "after": {}},
        "target_type": None,
        "target": None,
        "created_at": datetime.utcnow(),
        "success": True,
        "rest_api_path": f"{request.method} {request.path}",
    })
    log.info("AUDIT_LOG in middleware before: {}", audit_log_data.get())

    try:
        return await handler(request)
    except Exception:
        audit_log_data.set(
            updated_data(
                target_data=audit_log_data.get(),
                values_to_update={
                    "success": False,
                },
            )
        )
        raise
    finally:
        try:
            log.info("AUDIT_LOG in after middleware try: {}", audit_log_data.get())
            async with root_ctx.db.begin_session() as session:
                query = sa.insert(audit_logs, audit_log_data.get())
                await session.execute(query)
        except Exception as e:
            log.error("Failed to write audit log {}", e)


def updated_data(target_data: dict[str, Any], values_to_update: dict[str, Any]) -> dict[str, Any]:
    current_audit_log_data = target_data.copy()
    return deep_update(current_audit_log_data, values_to_update)


def empty_after_data(new_data: dict[str, Any]) -> dict[str, Any]:
    current_audit_log_data = new_data.copy()
    current_audit_log_data["data"]["after"] = {}
    return current_audit_log_data


def dictify_entry(entry: Mapping[str, Any]) -> dict[str, str]:
    return {k: str(v) for k, v in dict(entry).items()}
