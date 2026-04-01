from typing import cast

from .session import Session as SyncSession


def is_admin(session: SyncSession) -> bool:
    return cast(bool, session.KeyPair(session.config.access_key).info()["is_admin"])
