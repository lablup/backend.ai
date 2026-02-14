from collections.abc import Mapping
from datetime import datetime
from typing import Protocol, runtime_checkable

from yarl import URL

from ai.backend.client.config import get_env
from ai.backend.common.auth.utils import generate_signature


@runtime_checkable
class AuthStrategy(Protocol):
    def sign(
        self,
        method: str,
        version: str,
        endpoint: URL,
        date: datetime,
        rel_url: str,
        content_type: str,
    ) -> Mapping[str, str]: ...


class HMACAuth:
    def __init__(
        self,
        access_key: str,
        secret_key: str,
        hash_type: str = "sha256",
    ) -> None:
        self.access_key: str = access_key
        self.secret_key: str = secret_key
        self.hash_type: str = hash_type

    def sign(
        self,
        method: str,
        version: str,
        endpoint: URL,
        date: datetime,
        rel_url: str,
        content_type: str,
    ) -> Mapping[str, str]:
        headers, _ = generate_signature(
            method=method,
            version=version,
            endpoint=endpoint,
            date=date,
            rel_url=rel_url,
            content_type=content_type,
            access_key=self.access_key,
            secret_key=self.secret_key,
            hash_type=self.hash_type,
        )
        return headers

    @classmethod
    def from_env(cls) -> "HMACAuth":
        access_key: str = get_env("ACCESS_KEY", "")
        secret_key: str = get_env("SECRET_KEY", "")
        return cls(access_key=access_key, secret_key=secret_key)
