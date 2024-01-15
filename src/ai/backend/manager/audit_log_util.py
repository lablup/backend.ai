import contextvars
import enum
import functools
import inspect
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

__all__ = (
    "audit_log_middleware",
    "audit_log_data",
    "set_audit_log_action_target_decorator",
    "update_audit_log_target_field",
    "update_after_data",
    "update_before_data",
    "update_audit_log_success_state",
    "empty_after_data",
    "dictify_entry",
)


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


def updated_data(target_data: dict[str, Any], values_to_update: dict[str, Any]) -> dict[str, Any]:
    current_audit_log_data = target_data.copy()
    return deep_update(current_audit_log_data, values_to_update)


def update_audit_log_by_field_name(field_to_update: str, value: Any) -> None:
    audit_log_data.set(
        updated_data(
            target_data=audit_log_data.get(),
            values_to_update={
                field_to_update: value,
            },
        )
    )


class ArgNameEnum(str, enum.Enum):
    REQUEST = "request"
    PARAMS = "params"
    REQUEST_MATCH_INFO = "request"


def set_audit_log_action_target_decorator(
    *,
    action: AuditLogAction,
    arg_name_enum: ArgNameEnum = ArgNameEnum.REQUEST,
    target_path: list[str] = [],
    nullable: bool = False,
):
    arg_name_str = arg_name_enum.value

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            def process_target() -> None:
                sig = inspect.signature(func)
                bound_args = sig.bind(*args, **kwargs)
                bound_args.apply_defaults()
                if arg_name_str not in bound_args.arguments:
                    raise KeyError(
                        f"Argument '{arg_name_str}' not found in function '{func.__name__}'"
                    )

                arg_value: web.Request | Any = bound_args.arguments[arg_name_str]

                if arg_name_enum == ArgNameEnum.REQUEST_MATCH_INFO:
                    result = arg_value.match_info[target_path[0]]
                else:
                    result = recursive_find(arg_value, target_path)

                update_audit_log_target_field(result)

            def recursive_find(obj: Any, now_path: list[str]) -> Any:
                if not now_path:
                    return obj
                if obj is None or not isinstance(obj, dict):
                    return None

                next_obj = obj.get(now_path[0])
                if next_obj is None:
                    raise KeyError(f"KeyError '{now_path[0]}'")

                return recursive_find(next_obj, now_path[1:])

            # Update action
            update_audit_log_by_field_name("action", action)

            # Process target
            if not nullable:
                process_target()

            # Call the original function
            return func(*args, **kwargs)

        return wrapper

    return decorator


def update_audit_log_target_field(value: str) -> None:
    update_audit_log_by_field_name("target", value)


def update_after_data(data_to_insert: dict[str, Any] | Iterable[dict[str, Any]]) -> None:
    update_audit_log_by_field_name("data", {"after": data_to_insert})


def update_before_data(data_to_insert: dict[str, Any] | Iterable[dict[str, Any]]) -> None:
    update_audit_log_by_field_name("data", {"before": data_to_insert})


def update_audit_log_success_state(success: bool) -> None:
    update_audit_log_by_field_name("success", success)


def empty_after_data(new_data: dict[str, Any]) -> None:
    current_audit_log_data = new_data.copy()
    current_audit_log_data["data"]["after"] = {}
    audit_log_data.set(current_audit_log_data)


def dictify_entry(entry: Mapping[str, Any]) -> dict[str, str]:
    return {k: str(v) for k, v in dict(entry).items()}
