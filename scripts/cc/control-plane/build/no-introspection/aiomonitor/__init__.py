__version__ = "0.0.0+absent"


class Absent(RuntimeError):
    pass


class Monitor:
    def __init__(self, *args, **kwargs):
        self.prompt = ""
        self.console_locals = {}

    def start(self):
        raise Absent(
            "the live introspection console is not built into confidential images"
        )

    def close(self):
        pass


def start_monitor(*args, **kwargs):
    raise Absent("the live introspection console is not built into confidential images")
