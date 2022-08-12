import asyncio
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import aioredis
from ai.backend.cli.interaction import ask_host, ask_number, ask_string


def config_redis(config_json: dict) -> dict:
    try:
        if config_json.get("redis") is None:
            raise KeyError
        elif type(config_json.get("redis")) != dict:
            raise TypeError
        redis_config: dict = dict(config_json["redis"])
        while True:
            redis_host_str, redis_port_str = str(redis_config.get("addr")).split(":")
            redis_host = ask_host("Redis host: ", str(redis_host_str))
            if type(redis_port_str) != str:
                raise TypeError
            redis_port = ask_number("Redis port: ", int(redis_port_str), 1, 65535)
            redis_password = ask_string("Redis password", use_default=False)
            if redis_password:
                redis_client = aioredis.Redis(
                    host=redis_host,
                    port=redis_port,
                    password=redis_password)
            else:
                redis_client = aioredis.Redis(host=redis_host, port=redis_port)

            try:
                loop = asyncio.get_event_loop()
                coroutine = redis_client.get("")
                loop.run_until_complete(coroutine)
                coroutine = redis_client.close()
                loop.run_until_complete(coroutine)
                config_json["redis"]["addr"] = f"{redis_host}:{redis_port}"
                config_json["redis"]["password"] = redis_password
                break
            except (aioredis.exceptions.ConnectionError, aioredis.exceptions.BusyLoadingError):
                print("Cannot connect to etcd. Please input etcd information again.")

        while True:
            timezone = input("System timezone: ")
            try:
                _ = ZoneInfo(timezone)
                config_json["system"]["timezone"] = timezone
                break
            except (ValueError, ZoneInfoNotFoundError):
                print('Please input correct timezone.')
        return config_json
    except ValueError:
        raise ValueError
