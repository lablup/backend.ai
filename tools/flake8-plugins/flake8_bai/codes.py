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
    DTO_DATACLASS = ("BAI201", "common DTO must be a pydantic model, not a dataclass")
    DTO_SCHEMA_BASE = (
        "BAI202",
        "v2 DTO inherits BaseRequestModel or BaseResponseModel, not BackendAISchema",
    )
    DTO_CONVERSION = (
        "BAI203",
        "no to_*/from_* conversion method in a v2 DTO; convert in the adapter",
    )
    CLI_DTO_IMPORT = ("BAI204", "CLI v2 imports ai.backend.common.dto inside the command function")
    LAZY_GROUP_TARGET = ("BAI401", "LazyGroup import_name points at a missing module or name")
    ADMIN_RESOLVER_CHECK = ("BAI402", "admin_ resolver must call check_admin_only() first")
    STORAGE_MODULE_HANDLER = ("BAI403", "storage api handler must be a handler class method")
    APPPROXY_NATIVE_ENUM = ("BAI404", "App Proxy column must not use a native ENUM type")

    @property
    def code(self) -> str:
        return self.value[0]

    @property
    def message(self) -> str:
        return self.value[1]
