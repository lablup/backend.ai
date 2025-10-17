from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession as SASession


@dataclass
class SessionWrapper:
    db_session: SASession
