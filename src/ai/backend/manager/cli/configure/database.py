import psycopg2
from ai.backend.cli.interaction import ask_string_in_array, ask_host, ask_number, ask_string
from tomlkit.items import Table, InlineTable


def config_database(config_toml: dict) -> tuple[dict, str, str, str, str, int]:
    # db section
    try:
        if config_toml.get("db") is None:
            raise KeyError
        elif type(config_toml.get("db")) != Table:
            raise TypeError
        database_config: dict = dict(config_toml["db"])

        database_type = ask_string_in_array("Database type", ["postgresql"], "postgresql")
        config_toml["db"]["type"] = database_type

        while True:
            try:
                if database_config.get("addr") is None:
                    raise KeyError
                elif type(database_config.get("addr")) != InlineTable:
                    raise TypeError
                database_address: dict = dict(database_config["addr"])
                database_host = ask_host("Database host: ", str(database_address.get("host")))
                if type(database_address.get("port")) != str:
                    database_port = ask_number("Database port: ",
                                               int(database_address["port"]), 1, 65535)
                else:
                    raise TypeError
                database_name = ask_string("Database name", str(database_config.get("name")))
                database_user = ask_string("Database user", str(database_config.get("user")))
                database_password = ask_string("Database password", use_default=False)
                if check_database_health(
                    database_host,
                    database_port,
                    database_name,
                    database_user,
                    database_password,
                ):
                    config_toml["db"]["addr"] = {"host": database_address, "port": database_port}
                    config_toml["db"]["name"] = database_name
                    config_toml["db"]["user"] = database_user
                    config_toml["db"]["password"] = database_password
                    break
            except ValueError:
                raise ValueError
        return config_toml, database_user, database_password, database_name, database_host, database_port
    except ValueError:
        raise ValueError


def check_database_health(host: str, port: int, database_name: str, user: str, password: str):
    try:
        database_client = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            dbname=database_name,
        )
        database_client.close()
        return True
    except Exception as e:
        print(e)
        return False
