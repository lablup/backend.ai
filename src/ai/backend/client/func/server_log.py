from typing import (
    Union,
    Sequence,
    Mapping,
)

from .base import api_function, BaseFunction
from ..request import Request

__all__ = (
    'ServerLog',
)


class ServerLog(BaseFunction):
    '''
    Provides a shortcut of :func:`Admin.query()
    <ai.backend.client.admin.Admin.query>` that fetches various server logs.
    '''

    @api_function
    @classmethod
    async def list(
        cls,
        mark_read: bool = False,
        page_size: int = 20,
        page_no: int = 1,
    ) -> Sequence[dict]:
        '''
        Fetches server (error) logs.

        :param mark_read: Mark read flog for server logs being fetched.
        :param page_size: Number of logs to fetch (from latest log).
        :param page_no: Page number to fetch.
        '''
        params: Mapping[str, Union[str, int]] = {
            'mark_read': str(mark_read),
            'page_size': page_size,
            'page_no': page_no,
        }
        rqst = Request('GET', '/logs/error', params=params)
        async with rqst.fetch() as resp:
            return await resp.json()
