from ai.backend.client.request import Request

from .base import BaseFunction, api_function

__all__ = ("Permission",)


class Permission(BaseFunction):
    @api_function
    @classmethod
    async def get(cls):
        rqst = Request("GET", "/acl")
        async with rqst.fetch() as resp:
            return await resp.json()
