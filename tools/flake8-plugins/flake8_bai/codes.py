import enum


class BAICode(enum.Enum):
    """Rule codes of the plugin.

    BAI0xx: package structure, BAI1xx: manager data and services, BAI2xx: DTO,
    BAI3xx: repositories, models and migrations, BAI4xx: CLI, GQL, storage and App Proxy.
    """

    INIT_IMPORT = ("BAI001", "import in a manager __init__.py; import from the defining module")
    DATA_NOT_FROZEN = ("BAI101", "manager data dataclass must be @dataclass(frozen=True)")
    ACTION_NOT_FROZEN = ("BAI102", "Action and ActionResult must be @dataclass(frozen=True)")
    ACTION_PAIR = ("BAI103", "one Action and ActionResult pair per file")

    @property
    def code(self) -> str:
        return self.value[0]

    @property
    def message(self) -> str:
        return self.value[1]
