from __future__ import annotations

import enum
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager as actxmgr
from datetime import UTC, datetime
from pathlib import PurePath
from typing import Any, Optional

import trafaret as t
from aiohttp import web

from ai.backend.common.json import dump_json_str
from ai.backend.logging import BraceStyleAdapter

from .errors import (
    InvalidConfigurationSourceError,
    InvalidPathError,
)
from .volumes.types import LoggingInternalMeta

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class CheckParamSource(enum.Enum):
    BODY = 0
    QUERY = 1


def fstime2datetime(t: float | int) -> datetime:
    return datetime.fromtimestamp(t, tz=UTC)


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
            raise InvalidConfigurationSourceError("Invalid source for check_params() helper")
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
        ) from e
    except NotImplementedError as e:
        raise web.HTTPBadRequest(
            text=dump_json_str(
                {
                    "type": "https://api.backend.ai/probs/storage/unsupported-operation",
                    "title": "Unsupported operation by the storage backend",
                },
            ),
            content_type="application/problem+json",
        ) from e


async def log_manager_api_entry(
    log: logging.Logger | BraceStyleAdapter,
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
            relpaths = params["relpaths"]
            paths_summary = str(relpaths[0]) + "..." if relpaths else "(empty)"
            log.info(
                "ManagerAPI::{}(v:{}, f:{}, p*:{})",
                name.upper(),
                params["volume"],
                params["vfid"],
                paths_summary,
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
    log: logging.Logger | BraceStyleAdapter,
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
    log: logging.Logger | BraceStyleAdapter,
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
        InvalidPathError: If the filepath is empty, contains invalid characters, or attempts path traversal
    """
    if not filepath:
        raise InvalidPathError("Filepath cannot be empty")

    # Convert to PurePath to handle cross-platform path normalization
    path = PurePath(filepath)

    # Check for path traversal attempts
    for part in path.parts:
        if part in (".", ".."):
            raise InvalidPathError(f"Path traversal not allowed: {filepath}")
        if "\x00" in part:  # Null byte
            raise InvalidPathError(f"Invalid character in filepath: {filepath}")

    # Convert back to string with forward slashes (POSIX style)
    normalized = str(path).replace("\\", "/")

    # Remove leading slash if present (we want relative paths)
    return normalized.removeprefix("/")
