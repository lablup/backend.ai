from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import redis

from ai.backend.cli.interaction import ask_host, ask_port, ask_string


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
            redis_port = ask_port("Redis port", default=int(redis_port_str))
            redis_password = ask_string("Redis password", default=None)
            redis_client = redis.Redis(
                host=redis_host,
                port=redis_port,
                password=redis_password,
            )
            try:
                redis_client.ping()
                redis_client.close()
                config_json["redis"]["addr"] = f"{redis_host}:{redis_port}"
                if redis_password:
                    config_json["redis"]["password"] = redis_password
                break
            except (redis.exceptions.ConnectionError, redis.exceptions.BusyLoadingError):
                print("Cannot connect to etcd. Please input etcd information again.")

        while True:
            timezone = input("System timezone: ")
            try:
                _ = ZoneInfo(timezone)
                config_json["system"]["timezone"] = timezone
                break
            except (ValueError, ZoneInfoNotFoundError):
                print("Please input correct timezone.")
        return config_json
    except ValueError:
        raise ValueError
