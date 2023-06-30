import enum
import json
import logging
from contextlib import asynccontextmanager as actxmgr
from datetime import datetime
from datetime import timezone as tz
from typing import Any, AsyncIterator, Optional, Union

import trafaret as t
from aiohttp import web

from ai.backend.common.logging import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]


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
                text=json.dumps(
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
            text=json.dumps(
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
            text=json.dumps(
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
