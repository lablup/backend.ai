from .session import Session as SyncSession


def is_admin(session: SyncSession) -> bool:
    return session.KeyPair(session.config.access_key).info()["is_admin"]
