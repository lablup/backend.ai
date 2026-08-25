from dataclasses import dataclass

from ai.backend.manager.services.session.base import SessionAction


@dataclass
class SessionFileAction(SessionAction):
    """Base for an operation on the files inside a session.

    Answered for by the session: what is touched lives inside it and holds no
    membership of its own.
    """
