import enum


class LogLevel(enum.StrEnum):
    CRITICAL = "CRITICAL"
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"
    DEBUG = "DEBUG"
    NOTSET = "NOTSET"


class LogFormat(enum.StrEnum):
    SIMPLE = enum.auto()
    VERBOSE = enum.auto()
