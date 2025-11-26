from typing import Optional

from aiohttp import web


class UnauthorizedPurityClient(web.HTTPInternalServerError):
    def __init__(self, msg: Optional[str] = None) -> None:
        super().__init__(reason=msg)
