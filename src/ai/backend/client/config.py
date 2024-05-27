import enum
import os
import random
import re
from pathlib import Path
from typing import (
    Any,
    Callable,
    Iterable,
    List,
    Mapping,
    Optional,
    Sequence,
    Tuple,
    TypeVar,
    Union,
    cast,
)

import appdirs
from dotenv import find_dotenv, load_dotenv
from yarl import URL

__all__ = [
    "parse_api_version",
    "get_config",
    "set_config",
    "APIConfig",
    "API_VERSION",
    "DEFAULT_CHUNK_SIZE",
    "MAX_INFLIGHT_CHUNKS",
]


class Undefined(enum.Enum):
    token = object()


_config = None
_undefined = Undefined.token

API_VERSION = (8, "20240315")
MIN_API_VERSION = (7, "20230615")

DEFAULT_CHUNK_SIZE = 16 * (2**20)  # 16 MiB
MAX_INFLIGHT_CHUNKS = 4

local_state_path = Path(appdirs.user_state_dir("backend.ai", "Lablup"))
local_cache_path = Path(appdirs.user_cache_dir("backend.ai", "Lablup"))


def parse_api_version(value: str) -> Tuple[int, str]:
    match = re.search(r"^v(?P<major>\d+)\.(?P<date>\d{8})$", value)
    if match is not None:
        return int(match.group(1)), match.group(2)
    raise ValueError("Could not parse the given API version string", value)


T = TypeVar("T")


def default_clean(v: T | Any) -> T:
    return cast(T, v)


def get_env(
    key: str,
    default: Union[str, Mapping, Undefined] = _undefined,
    *,
    clean: Callable[[Any], T] = default_clean,
) -> T:
    """
    Retrieves a configuration value from the environment variables.
    The given *key* is uppercased and prefixed by ``"BACKEND_"`` and then
    ``"SORNA_"`` if the former does not exist.

    :param key: The key name.
    :param default: The default value returned when there is no corresponding
        environment variable.
    :param clean: A single-argument function that is applied to the result of lookup
        (in both successes and the default value for failures).
        The default is returning the value as-is.

    :returns: The value processed by the *clean* function.
    """
    load_dotenv(dotenv_path=find_dotenv(usecwd=True), override=True)
    key = key.upper()
    raw = os.environ.get("BACKEND_" + key)
    if raw is None:
        raw = os.environ.get("SORNA_" + key)
    if raw is None:
        if default is _undefined:
            raise KeyError(key)
        result = default
    else:
        result = raw
    return clean(result)


def bool_env(v: str) -> bool:
    v = v.lower()
    if v in ("y", "yes", "t", "true", "1"):
        return True
    if v in ("n", "no", "f", "false", "0"):
        return False
    raise ValueError("Unrecognized value of boolean environment variable", v)


def _clean_urls(v: Union[URL, str]) -> List[URL]:
    if isinstance(v, URL):
        return [v]
    urls = []
    if isinstance(v, str):
        for entry in v.split(","):
            url = URL(entry)
            if not url.is_absolute():
                raise ValueError("URL {} is not absolute.".format(url))
            urls.append(url)
    return urls


def _clean_tokens(v: str) -> Tuple[str, ...]:
    if not v:
        return tuple()
    return tuple(v.split(","))


def _clean_address_map(v: Union[str, Mapping]) -> Mapping:
    if isinstance(v, dict):
        return v
    if not isinstance(v, str):
        raise ValueError(
            f'Storage proxy address map has invalid type "{type(v)}", expected str or dict.',
        )
    override_map = {}
    for assignment in v.split(","):
        try:
            k, _, v = assignment.partition("=")
            if k == "" or v == "":
                raise ValueError
        except ValueError:
            raise ValueError(f"{v} is not a valid mapping expression")
        else:
            override_map[k] = v
    return override_map


class APIConfig:
    """
    Represents a set of API client configurations.
    The access key and secret key are mandatory -- they must be set in either
    environment variables or as the explicit arguments.

    :param endpoint: The URL prefix to make API requests via HTTP/HTTPS.
        If this is given as ``str`` and contains multiple URLs separated by comma,
        the underlying HTTP request-response facility will perform client-side
        load balancing and automatic fail-over using them, assuming that all those
        URLs indicates a single, same cluster.
        The users of the API and CLI will get network connection errors only when
        all of the given endpoints fail -- intermittent failures of a subset of endpoints
        will be hidden with a little increased latency.
    :param endpoint_type: Either ``"api"`` or ``"session"``.
        If the endpoint type is ``"api"`` (the default if unspecified), it uses the access key and
        secret key in the configuration to access the manager API server directly.
        If the endpoint type is ``"session"``, it assumes the endpoint is a Backend.AI console server
        which provides cookie-based authentication with username and password.
        In the latter, users need to use ``backend.ai login`` and ``backend.ai logout`` to
        manage their sign-in status, or the API equivalent in
        :meth:`~ai.backend.client.auth.Auth.login` and
        :meth:`~ai.backend.client.auth.Auth.logout` methods.
    :param version: The API protocol version.
    :param user_agent: A custom user-agent string which is sent to the API
        server as a ``User-Agent`` HTTP header.
    :param access_key: The API access key.  If deliberately set to an empty string, the API
        requests will be made without signatures (anonymously).
    :param secret_key: The API secret key.
    :param hash_type: The hash type to generate per-request authentication
        signatures.
    :param vfolder_mounts: A list of vfolder names (that must belong to the given
        access key) to be automatically mounted upon any
        :func:`Kernel.get_or_create()
        <ai.backend.client.kernel.Kernel.get_or_create>` calls.
    """

    DEFAULTS: Mapping[str, Union[str, Mapping]] = {
        "endpoint": "https://api.cloud.backend.ai",
        "endpoint_type": "api",
        "version": f"v{API_VERSION[0]}.{API_VERSION[1]}",
        "hash_type": "sha256",
        "domain": "default",
        "group": "default",
        "storage_proxy_address_map": {},
        "connection_timeout": "10.0",
        "read_timeout": "0",
    }
    """
    The default values for config parameters settable via environment variables
    except the access and secret keys.
    """

    _endpoints: List[URL]
    _group: str
    _hash_type: str
    _skip_sslcert_validation: bool
    _version: str

    def __init__(
        self,
        *,
        endpoint: Union[URL, str] = None,
        endpoint_type: str = None,
        domain: str = None,
        group: str = None,
        storage_proxy_address_map: Mapping[str, str] = None,
        version: str = None,
        user_agent: str = None,
        access_key: str = None,
        secret_key: str = None,
        hash_type: str = None,
        vfolder_mounts: Iterable[str] = None,
        skip_sslcert_validation: bool = None,
        connection_timeout: float = None,
        read_timeout: float = None,
        announcement_handler: Callable[[str], None] = None,
    ) -> None:
        from . import get_user_agent

        self._endpoints = (
            _clean_urls(endpoint)
            if endpoint
            else get_env("ENDPOINT", self.DEFAULTS["endpoint"], clean=_clean_urls)
        )
        random.shuffle(self._endpoints)
        self._endpoint_type = (
            endpoint_type
            if endpoint_type is not None
            else get_env("ENDPOINT_TYPE", self.DEFAULTS["endpoint_type"], clean=str)
        )
        self._domain = (
            domain if domain is not None else get_env("DOMAIN", self.DEFAULTS["domain"], clean=str)
        )
        self._group = (
            group if group is not None else get_env("GROUP", self.DEFAULTS["group"], clean=str)
        )
        self._storage_proxy_address_map = (
            storage_proxy_address_map
            if storage_proxy_address_map is not None
            else get_env(
                "OVERRIDE_STORAGE_PROXY",
                self.DEFAULTS["storage_proxy_address_map"],
                # The shape of this env var must be like "X1=Y1,X2=Y2"
                clean=_clean_address_map,
            )
        )
        self._version = version if version is not None else default_clean(self.DEFAULTS["version"])
        self._user_agent = user_agent if user_agent is not None else get_user_agent()
        if self._endpoint_type == "api":
            self._access_key = access_key if access_key is not None else get_env("ACCESS_KEY", "")
            self._secret_key = secret_key if secret_key is not None else get_env("SECRET_KEY", "")
        else:
            self._access_key = "dummy"
            self._secret_key = "dummy"
        self._hash_type = (
            hash_type.lower() if hash_type is not None else cast(str, self.DEFAULTS["hash_type"])
        )
        arg_vfolders = set(vfolder_mounts) if vfolder_mounts else set()
        env_vfolders = set(get_env("VFOLDER_MOUNTS", "", clean=_clean_tokens))
        self._vfolder_mounts = [*(arg_vfolders | env_vfolders)]
        # prefer the argument flag and fallback to env if the flag is not set.
        if skip_sslcert_validation:
            self._skip_sslcert_validation = True
        else:
            self._skip_sslcert_validation = get_env(
                "SKIP_SSLCERT_VALIDATION",
                "no",
                clean=bool_env,
            )
        self._connection_timeout = (
            connection_timeout
            if connection_timeout is not None
            else get_env("CONNECTION_TIMEOUT", self.DEFAULTS["connection_timeout"], clean=float)
        )
        self._read_timeout = (
            read_timeout
            if read_timeout is not None
            else get_env("READ_TIMEOUT", self.DEFAULTS["read_timeout"], clean=float)
        )
        self._announcement_handler = announcement_handler

    @property
    def is_anonymous(self) -> bool:
        return self._access_key == ""

    @property
    def endpoint(self) -> URL:
        """
        The currently active endpoint URL.
        This may change if there are multiple configured endpoints
        and the current one is not accessible.
        """
        return self._endpoints[0]

    @property
    def endpoints(self) -> Sequence[URL]:
        """All configured endpoint URLs."""
        return self._endpoints

    def rotate_endpoints(self):
        if len(self._endpoints) > 1:
            item = self._endpoints.pop(0)
            self._endpoints.append(item)

    def load_balance_endpoints(self):
        pass

    @property
    def endpoint_type(self) -> str:
        """
        The configured endpoint type.
        """
        return self._endpoint_type

    @property
    def domain(self) -> str:
        """The configured domain."""
        return self._domain

    @property
    def group(self) -> str:
        """The configured group."""
        return self._group

    @property
    def storage_proxy_address_map(self) -> Mapping[str, str]:
        """The storage proxy address map for overriding."""
        return self._storage_proxy_address_map

    @property
    def user_agent(self) -> str:
        """The configured user agent string."""
        return self._user_agent

    @property
    def access_key(self) -> str:
        """The configured API access key."""
        return self._access_key

    @property
    def secret_key(self) -> str:
        """The configured API secret key."""
        return self._secret_key

    @property
    def version(self) -> str:
        """The configured API protocol version."""
        return self._version

    @property
    def hash_type(self) -> str:
        """The configured hash algorithm for API authentication signatures."""
        return self._hash_type

    @property
    def vfolder_mounts(self) -> Sequence[str]:
        """The configured auto-mounted vfolder list."""
        return self._vfolder_mounts

    @property
    def skip_sslcert_validation(self) -> bool:
        """Whether to skip SSL certificate validation for the API gateway."""
        return self._skip_sslcert_validation

    @property
    def connection_timeout(self) -> float:
        """The maximum allowed duration for making TCP connections to the server."""
        return self._connection_timeout

    @property
    def read_timeout(self) -> float:
        """The maximum allowed waiting time for the first byte of the response from the server."""
        return self._read_timeout

    @property
    def announcement_handler(self) -> Optional[Callable[[str], None]]:
        """The announcement handler to display server-set announcements."""
        return self._announcement_handler


def get_config() -> APIConfig:
    """
    Returns the configuration for the current process.
    If there is no explicitly set :class:`APIConfig` instance,
    it will generate a new one from the current environment variables
    and defaults.
    """
    global _config
    if _config is None:
        _config = APIConfig()
    return _config


def set_config(conf: Optional[APIConfig]) -> None:
    """
    Sets the configuration used throughout the current process.
    """
    global _config
    _config = conf
