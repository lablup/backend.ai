from ..request import Request
from .base import BaseFunction, api_function

__all__ = ("RateLimit",)


class RateLimit(BaseFunction):
    """
    Provides RateLimiting API functions.
    """

    @api_function
    @classmethod
    async def get_hot_anonymous_clients(cls):
        """ """
        rqst = Request("GET", "/ratelimit/hot_anonymous_clients")
        async with rqst.fetch() as resp:
            return await resp.json()
