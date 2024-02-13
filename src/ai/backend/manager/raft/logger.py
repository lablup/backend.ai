from typing import Any


class Logger:
    def __init__(self, logger: Any) -> None:
        self.logger = logger

    def trace(self, message):
        self.logger.debug(message)

    def debug(self, message):
        self.logger.debug(message)

    def info(self, message):
        self.logger.info(message)

    def warn(self, message):
        self.logger.warning(message)

    def error(self, message):
        self.logger.error(message)

    def fatal(self, message):
        self.logger.error(message)
        assert False, "Fatal error occurred: " + message
