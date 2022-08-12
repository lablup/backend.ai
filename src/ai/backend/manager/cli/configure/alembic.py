from configparser import ConfigParser

from ai.backend.cli.interaction import ask_string, ask_number, ask_string_in_array


def config_alembic(config_parser: ConfigParser,
                   database_user: str,
                   database_password: str,
                   database_name: str,
                   database_host: str,
                   database_port: int) -> ConfigParser:
    script_location = ask_string("Script location: ", config_parser["alembic"]["script_location"])
    config_parser["alembic"]["script_location"] = script_location

    file_template = ask_string("File template: ", use_default=False)
    if file_template:
        config_parser["alembic"]["file_template"] = file_template
    else:
        config_parser["alembic"].pop("file_template")

    timezone = ask_string("Timezone: ", use_default=False)
    if file_template:
        config_parser["alembic"]["timezone"] = timezone
    else:
        config_parser["alembic"].pop("timezone")

    truncate_slug_length: int = ask_number("Max length of slug field(If you don\'t want to use, "
                                           "just leave default value): ", 0, 0, 40)
    if truncate_slug_length > 0:
        config_parser["alembic"]["truncate_slug_length"] = str(truncate_slug_length)
    else:
        config_parser["alembic"].pop("truncate_slug_length")

    revision_environment = ask_string_in_array("Revision Environment", ["true", "false", ""],
                                               config_parser["alembic"]["revision_environment"])
    if revision_environment:
        config_parser["alembic"]["revision_environment"] = revision_environment
    else:
        config_parser["alembic"].pop("revision_environment")

    sourceless = ask_string_in_array("Sourceless(set to 'true' to allow .pyc and .pyo files "
                                     "without a source .py)", ["true", "false", ""], "true")
    if sourceless:
        config_parser["alembic"]["sourceless"] = sourceless
    else:
        config_parser["alembic"].pop("sourceless")

    # modify database scheme
    if all([x is not None for x in
            [database_user, database_password, database_name, database_host, database_port]]):
        config_parser["alembic"]["sqlalchemy.url"] = \
            f"postgresql://{database_user}:{database_password}" \
            f"@{database_host}:{database_port}/{database_name}"

    logger_keys = ask_string("Logger keys: ", default=config_parser["loggers"]["keys"])
    config_parser["loggers"]["keys"] = logger_keys
    handlers_keys = ask_string("Handlers keys: ", default=config_parser["handlers"]["keys"])
    config_parser["handlers"]["keys"] = handlers_keys
    formatters_keys = ask_string("Formatters keys: ", default=config_parser["formatters"]["keys"])
    config_parser["formatters"]["keys"] = formatters_keys

    logger_root_level = ask_string("Logger root level", default=config_parser["logger_root"]["level"])
    logger_root_handlers = ask_string("Logger root handlers",
                                      default=config_parser["logger_root"]["handlers"])
    logger_root_qualname = ask_string("Logger root qualname",
                                      default=config_parser["logger_root"]["qualname"])
    config_parser["logger_root"]["level"] = logger_root_level
    config_parser["logger_root"]["handlers"] = logger_root_handlers
    config_parser["logger_root"]["qualname"] = logger_root_qualname

    logger_sqlalchemy_level = ask_string("Logger sqlalchemy level",
                                         default=config_parser["logger_sqlalchemy"]["level"])
    logger_sqlalchemy_handlers = ask_string("Logger sqlalchemy handlers",
                                            default=config_parser["logger_sqlalchemy"]["handlers"])
    logger_sqlalchemy_qualname = ask_string("Logger sqlalchemy qualname",
                                            default=config_parser["logger_sqlalchemy"]["qualname"])
    config_parser["logger_sqlalchemy"]["level"] = logger_sqlalchemy_level
    config_parser["logger_sqlalchemy"]["handlers"] = logger_sqlalchemy_handlers
    config_parser["logger_sqlalchemy"]["qualname"] = logger_sqlalchemy_qualname

    logger_alembic_level = ask_string("Logger alembic level",
                                      default=config_parser["logger_alembic"]["level"])
    logger_alembic_handlers = ask_string("Logger alembic handlers",
                                         default=config_parser["logger_alembic"]["handlers"])
    logger_alembic_qualname = ask_string("Logger alembic qualname",
                                         default=config_parser["logger_alembic"]["qualname"])
    config_parser["logger_alembic"]["level"] = logger_alembic_level
    config_parser["logger_alembic"]["handlers"] = logger_alembic_handlers
    config_parser["logger_alembic"]["qualname"] = logger_alembic_qualname

    handler_console_class = ask_string("Handler console class",
                                       default=config_parser["handler_console"]["class"])
    handler_console_args = ask_string("Handler console args",
                                      default=config_parser["handler_console"]["args"])
    handler_console_level = ask_string("Handler console level",
                                       default=config_parser["handler_console"]["level"])
    handler_console_formatter = ask_string("Handler console formatter",
                                           default=config_parser["handler_console"]["formatter"])
    config_parser["handler_console"]["class"] = handler_console_class
    config_parser["handler_console"]["args"] = handler_console_args
    config_parser["handler_console"]["level"] = handler_console_level
    config_parser["handler_console"]["formatter"] = handler_console_formatter
    return config_parser
