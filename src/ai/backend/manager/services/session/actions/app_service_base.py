from dataclasses import dataclass

from ai.backend.manager.services.session.base import SessionAction


@dataclass
class SessionAppServiceAction(SessionAction):
    """Base for an operation on the services a session exposes.

    Answered for by the session: what is touched lives inside it and holds no
    membership of its own.
    """
