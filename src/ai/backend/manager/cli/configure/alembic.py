from configparser import ConfigParser

from ai.backend.cli.interaction import ask_string


def config_alembic(
    template: ConfigParser,
    database_user: str,
    database_password: str,
    database_name: str,
    database_host: str,
    database_port: int,
) -> ConfigParser:
    script_location = ask_string("Script location", default=template["alembic"]["script_location"])
    template["alembic"]["script_location"] = script_location

    file_template = ask_string("File template")
    if file_template:
        template["alembic"]["file_template"] = file_template
    else:
        template["alembic"].pop("file_template")

    timezone = ask_string("Timezone")
    if file_template:
        template["alembic"]["timezone"] = timezone
    else:
        template["alembic"].pop("timezone")

    # modify database scheme
    if all(
        [
            x is not None
            for x in [database_user, database_password, database_name, database_host, database_port]
        ]
    ):
        template["alembic"]["sqlalchemy.url"] = (
            f"postgresql://{database_user}:{database_password}"
            f"@{database_host}:{database_port}/{database_name}"
        )

    logger_keys = ask_string("Logger keys: ", default=template["loggers"]["keys"])
    template["loggers"]["keys"] = logger_keys
    handlers_keys = ask_string("Handlers keys: ", default=template["handlers"]["keys"])
    template["handlers"]["keys"] = handlers_keys
    formatters_keys = ask_string("Formatters keys: ", default=template["formatters"]["keys"])
    template["formatters"]["keys"] = formatters_keys

    logger_root_level = ask_string("Logger root level", default=template["logger_root"]["level"])
    logger_root_handlers = ask_string(
        "Logger root handlers", default=template["logger_root"]["handlers"]
    )
    logger_root_qualname = ask_string(
        "Logger root qualname", default=template["logger_root"]["qualname"]
    )
    template["logger_root"]["level"] = logger_root_level
    template["logger_root"]["handlers"] = logger_root_handlers
    template["logger_root"]["qualname"] = logger_root_qualname

    logger_sqlalchemy_level = ask_string(
        "Logger sqlalchemy level", default=template["logger_sqlalchemy"]["level"]
    )
    logger_sqlalchemy_handlers = ask_string(
        "Logger sqlalchemy handlers", default=template["logger_sqlalchemy"]["handlers"]
    )
    logger_sqlalchemy_qualname = ask_string(
        "Logger sqlalchemy qualname", default=template["logger_sqlalchemy"]["qualname"]
    )
    template["logger_sqlalchemy"]["level"] = logger_sqlalchemy_level
    template["logger_sqlalchemy"]["handlers"] = logger_sqlalchemy_handlers
    template["logger_sqlalchemy"]["qualname"] = logger_sqlalchemy_qualname

    logger_alembic_level = ask_string(
        "Logger alembic level", default=template["logger_alembic"]["level"]
    )
    logger_alembic_handlers = ask_string(
        "Logger alembic handlers", default=template["logger_alembic"]["handlers"]
    )
    logger_alembic_qualname = ask_string(
        "Logger alembic qualname", default=template["logger_alembic"]["qualname"]
    )
    template["logger_alembic"]["level"] = logger_alembic_level
    template["logger_alembic"]["handlers"] = logger_alembic_handlers
    template["logger_alembic"]["qualname"] = logger_alembic_qualname

    handler_console_class = ask_string(
        "Handler console class", default=template["handler_console"]["class"]
    )
    handler_console_args = ask_string(
        "Handler console args", default=template["handler_console"]["args"]
    )
    handler_console_level = ask_string(
        "Handler console level", default=template["handler_console"]["level"]
    )
    handler_console_formatter = ask_string(
        "Handler console formatter", default=template["handler_console"]["formatter"]
    )
    template["handler_console"]["class"] = handler_console_class
    template["handler_console"]["args"] = handler_console_args
    template["handler_console"]["level"] = handler_console_level
    template["handler_console"]["formatter"] = handler_console_formatter
    return template
