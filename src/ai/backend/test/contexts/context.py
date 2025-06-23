import enum
from abc import abstractmethod
from collections.abc import Mapping, MutableMapping
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Generic, Iterator, Optional, TypeVar, final

T = TypeVar("T")


class ContextName(enum.StrEnum):
    """
    Enum for context names used in the test framework.
    This enum provides a set of predefined context names that can be used to identify different contexts in the testing framework.
    """

    TEST_SPEC_META = "test_spec_meta"
    IMAGE = "image"
    CLIENT_SESSION = "client_session"
    ENDPOINT = "endpoint"
    KEYPAIR = "keypair"
    LOGIN_CREDENTIAL = "login_credential"
    SESSION = "session"
    SSE = "sse"
    BATCH_SESSION = "batch_session"
    CLUSTER_CONFIG = "cluster_config"
    CODE_EXECUTION = "code_execution"
    SESSION_TEMPLATE = "session_template"
    BOOTSTRAP_SCRIPT = "bootstrap_script"
    SESSION_IMAGIFY = "session_imagify"
    TEST_ERROR_OUTPUT_DIRECTORY = "test_error_output_directory"
    SESSION_DEPENDENCY = "session_dependency"
    VFOLDER = "vfolder"
    CREATED_VFOLDER_META = "created_vfolder_meta"

    CREATED_SESSION_META = "created_session_meta"
    CREATED_SESSION_TEMPLATE_ID = "created_session_template_id"


class BaseTestContext(Generic[T]):
    """
    Base class for tester's context management.
    This class provides a way to manage context variables for test scenarios.
    It uses `contextvars` to store the current value and provides methods to get and set this value.
    It is designed to be subclassed for specific test contexts.
    """

    _ctxvar: Optional[ContextVar[Optional[T]]] = None
    _used: MutableMapping[ContextName, "BaseTestContext"] = {}

    def __init_subclass__(cls):
        if cls._ctxvar is not None:
            raise RuntimeError(f"{cls.__name__} is already initialized")
        cls._ctxvar = ContextVar[T](f"{cls.__name__}_ctxvar", default=None)
        cls._used[cls.name()] = cls

    @classmethod
    @abstractmethod
    def name(cls) -> ContextName:
        """
        Get the name of the context
        :return: name of the context
        """
        raise NotImplementedError(
            f"{cls.__name__} must implement get_name method to return the context name"
        )

    @classmethod
    def used_contexts(cls) -> Mapping[ContextName, "BaseTestContext"]:
        """
        Get all used contexts
        :return: mapping of context names to context instances
        """
        return cls._used

    @classmethod
    @final
    def current(cls) -> T:
        """
        Get the current value from context
        :raises RuntimeError: if no value is set in the context (Tester must set it before using)
        """
        if cls._ctxvar is None:
            raise RuntimeError("Don't use BaseTestContext directly, subclass it instead")
        res = cls._ctxvar.get()
        if res is None:
            raise RuntimeError(f'No value is set in "{cls.name()}" context')
        return res

    @classmethod
    @final
    @contextmanager
    def with_current(cls, value: T) -> Iterator[None]:
        """Set the current value in the context"""
        if cls._ctxvar is None:
            raise RuntimeError("Don't use BaseTestContext directly, subclass it instead")
        token = cls._ctxvar.set(value)
        try:
            yield
        finally:
            cls._ctxvar.reset(token)
