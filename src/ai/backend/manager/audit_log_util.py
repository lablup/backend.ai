import contextvars
import functools
import logging
from datetime import datetime
from typing import Any, Iterable, Mapping

import sqlalchemy as sa
from aiohttp import web
from aiohttp.typedefs import Handler
from pydantic.v1.utils import deep_update

from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.manager.api.context import RootContext
from ai.backend.manager.models.audit_logs import AuditLogAction, AuditLogTargetType, audit_logs

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]

audit_log_data: contextvars.ContextVar[dict[str, Any]] = contextvars.ContextVar(
    "audit_log_data", default={}
)

# target


@web.middleware
async def audit_log_middleware(request: web.Request, handler: Handler) -> web.StreamResponse:
    # TODO: in near future we can change this condition to dict so we can add more conditions

    if request.method == "GET":
        return await handler(request)

    root_ctx: RootContext = request.app["_root.context"]
    user_uuid = str(request["user"]["uuid"])
    access_key = request["keypair"]["access_key"]
    user_email = request["user"]["email"]

    # "action": AuditLogAction.CREATE,
    # "target": folder_host,

    audit_log_data.set({
        "user_id": user_uuid,
        "access_key": access_key,
        "email": user_email,
        "action": None,
        "data": {"before": {}, "after": {}},
        "target_type": target_type_path_mapper(request),
        "target": None,
        "created_at": datetime.utcnow(),
        "success": True,
        "rest_api_path": f"{request.method} {request.path}",
    })
    log.info("AUDIT_LOG in middleware before: {}", audit_log_data.get())

    try:
        return await handler(request)
    except Exception:
        update_audit_log_success_state(False)
        raise
    finally:
        try:
            log.info("AUDIT_LOG in after middleware try: {}", audit_log_data.get())
            async with root_ctx.db.begin_session() as session:
                query = sa.insert(audit_logs, audit_log_data.get())
                await session.execute(query)
        except Exception as e:
            log.error("Failed to write audit log {}", e)


# target_type
def target_type_path_mapper(request: web.Request) -> AuditLogTargetType:
    prefix = request.path.split("/")[1]
    match prefix:
        case "users":
            raise ValueError(f"Unknown target type: {prefix}")
        case "keypairs":
            raise ValueError(f"Unknown target type: {prefix}")
        case "groups":
            raise ValueError(f"Unknown target type: {prefix}")
        case "folders":
            return AuditLogTargetType.VFOLDER
        case "compute-sessions":
            raise ValueError(f"Unknown target type: {prefix}")
    raise ValueError(f"Unknown action: {prefix}")


def set_audit_log_action_decorator(action: AuditLogAction):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            update_audit_log_field("action", action)
            return func(*args, **kwargs)

        return wrapper

    return decorator


def set_target_decorator(obj: Any, target_path: list[str]):
    def recursive_find(obj: Any, target_path: list[str]):
        if not target_path or obj is None:
            return obj
        else:
            return recursive_find(obj.get(target_path[0]), target_path[1:])

    def decorator(func):
        @functools.wraps(func)
        def wrapper(obj: Any, *args, **kwargs):
            target = recursive_find(obj, target_path)
            if target is None:
                output = "".join([f'["{item}"]' for item in target_path])
                raise ValueError(f"Target not found: Object{output}")

            update_audit_log_field("target", target)
            return func(target, *args, **kwargs)

        return wrapper

    return decorator


def update_audit_log_field(field_to_update: str, value: Any):
    audit_log_data.set(
        updated_data(
            target_data=audit_log_data.get(),
            values_to_update={
                field_to_update: value,
            },
        )
    )


def updated_data(target_data: dict[str, Any], values_to_update: dict[str, Any]) -> dict[str, Any]:
    current_audit_log_data = target_data.copy()
    return deep_update(current_audit_log_data, values_to_update)


def empty_after_data(new_data: dict[str, Any]) -> None:
    current_audit_log_data = new_data.copy()
    current_audit_log_data["data"]["after"] = {}
    audit_log_data.set(current_audit_log_data)


def update_after_data(data_to_insert: dict[str, Any] | Iterable[dict[str, Any]]):
    update_audit_log_field("data", {"after": data_to_insert})


def update_before_data(data_to_insert: dict[str, Any] | Iterable[dict[str, Any]]):
    update_audit_log_field("data", {"before": data_to_insert})


def update_audit_log_success_state(success: bool):
    update_audit_log_field("success", success)


def dictify_entry(entry: Mapping[str, Any]) -> dict[str, str]:
    return {k: str(v) for k, v in dict(entry).items()}
