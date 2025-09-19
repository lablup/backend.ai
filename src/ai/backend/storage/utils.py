import enum
import logging
from contextlib import asynccontextmanager as actxmgr
from datetime import datetime
from datetime import timezone as tz
from pathlib import PurePath
from typing import Any, AsyncIterator, Optional, Union

import trafaret as t
from aiohttp import web

from ai.backend.common.json import dump_json_str
from ai.backend.logging import BraceStyleAdapter

from .volumes.types import LoggingInternalMeta

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class CheckParamSource(enum.Enum):
    BODY = 0
    QUERY = 1


def fstime2datetime(t: Union[float, int]) -> datetime:
    return datetime.utcfromtimestamp(t).replace(tzinfo=tz.utc)


@actxmgr
async def check_params(
    request: web.Request,
    checker: Optional[t.Trafaret],
    *,
    read_from: CheckParamSource = CheckParamSource.BODY,
    auth_required: bool = True,
) -> AsyncIterator[Any]:
    if checker is None:
        if request.can_read_body:
            raise web.HTTPBadRequest(
                text=dump_json_str(
                    {
                        "type": "https://api.backend.ai/probs/storage/malformed-request",
                        "title": "Malformed request (request body should be empty)",
                    },
                ),
                content_type="application/problem+json",
            )
    else:
        if read_from == CheckParamSource.BODY:
            raw_params = await request.json()
        elif read_from == CheckParamSource.QUERY:
            raw_params = request.query
        else:
            raise ValueError("Invalid source for check_params() helper")
    try:
        if checker is None:
            yield None
        else:
            yield checker.check(raw_params)
    except t.DataError as e:
        log.debug("check_params IV error", exc_info=e)
        raise web.HTTPBadRequest(
            text=dump_json_str(
                {
                    "type": "https://api.backend.ai/probs/storage/invalid-api-params",
                    "title": "Invalid API parameters",
                    "data": e.as_dict(),
                },
            ),
            content_type="application/problem+json",
        )
    except NotImplementedError:
        raise web.HTTPBadRequest(
            text=dump_json_str(
                {
                    "type": "https://api.backend.ai/probs/storage/unsupported-operation",
                    "title": "Unsupported operation by the storage backend",
                },
            ),
            content_type="application/problem+json",
        )


async def log_manager_api_entry(
    log: Union[logging.Logger, BraceStyleAdapter],
    name: str,
    params: Any,
) -> None:
    if params is not None:
        if "src_vfid" in params and "dst_vfid" in params:
            log.info(
                "ManagerAPI::{}(v:{}, f:{} -> dst_v: {}, dst_f:{})",
                name.upper(),
                params["src_volume"],
                params["src_vfid"],
                params["dst_volume"],
                params["dst_vfid"],
            )
        elif "relpaths" in params:
            log.info(
                "ManagerAPI::{}(v:{}, f:{}, p*:{})",
                name.upper(),
                params["volume"],
                params["vfid"],
                str(params["relpaths"][0]) + "...",
            )
        elif "relpath" in params:
            log.info(
                "ManagerAPI::{}(v:{}, f:{}, p:{})",
                name.upper(),
                params["volume"],
                params["vfid"],
                params["relpath"],
            )
        elif "vfid" in params:
            log.info(
                "ManagerAPI::{}(v:{}, f:{})",
                name.upper(),
                params["volume"],
                params["vfid"],
            )
        elif "volume" in params:
            log.info(
                "ManagerAPI::{}(v:{})",
                name.upper(),
                params["volume"],
            )
        return
    log.info(
        "ManagerAPI::{}()",
        name.upper(),
    )


async def log_manager_api_entry_new(
    log: Union[logging.Logger, BraceStyleAdapter],
    name: str,
    params: Any,
) -> None:
    if params is None:
        log.info(
            "ManagerAPI::{}()",
            name.upper(),
        )
    elif isinstance(params, LoggingInternalMeta):
        log.info(
            "ManagerAPI::{}({})",
            name.upper(),
            params.to_logging_str(),
        )
    else:
        log.info(
            "ManagerAPI::{}({})",
            name.upper(),
            str(params),
        )


async def log_client_api_entry(
    log: Union[logging.Logger, BraceStyleAdapter],
    name: str,
    params: Any,
) -> None:
    if params is None:
        log.info(
            "ClientFacingAPI::{}()",
            name.upper(),
        )
    elif isinstance(params, LoggingInternalMeta):
        log.info(
            "ClientFacingAPI::{}({})",
            name.upper(),
            params.to_logging_str(),
        )
    else:
        log.info(
            "ClientFacingAPI::{}({})",
            name.upper(),
            str(params),
        )


def normalize_filepath(filepath: str) -> str:
    """
    Normalize a filepath by removing path traversal components and extra slashes.

    Args:
        filepath: The filepath to normalize

    Returns:
        Normalized filepath string

    Raises:
        ValueError: If the filepath contains invalid characters or path traversal
    """
    if not filepath:
        raise ValueError("Filepath cannot be empty")

    # Convert to PurePath to handle cross-platform path normalization
    path = PurePath(filepath)

    # Check for path traversal attempts
    for part in path.parts:
        if part in (".", ".."):
            raise ValueError(f"Path traversal not allowed: {filepath}")
        if "\x00" in part:  # Null byte
            raise ValueError(f"Invalid character in filepath: {filepath}")

    # Convert back to string with forward slashes (POSIX style)
    normalized = str(path).replace("\\", "/")

    # Remove leading slash if present (we want relative paths)
    if normalized.startswith("/"):
        normalized = normalized[1:]

    return normalized
