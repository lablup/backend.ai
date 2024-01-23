from typing import Any

import jinja2
from aiohttp import web
from redis.asyncio import Redis

from ai.backend.web.stats import WebStats

__all__ = (
    "redis_app_key",
    "config_app_key",
    "j2env_app_key",
    "stats_app_key",
)

redis_app_key = web.AppKey("redis", Redis)
config_app_key = web.AppKey("config", Any)
j2env_app_key = web.AppKey("j2env", jinja2.Environment)
stats_app_key = web.AppKey("stats", WebStats)
