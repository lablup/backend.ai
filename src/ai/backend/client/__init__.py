from pathlib import Path

from . import exceptions, session

__all__ = (
    *exceptions.__all__,
    *session.__all__,
)

__version__ = (Path(__file__).parent / "VERSION").read_text().strip()


def get_user_agent():
    return "Backend.AI Client for Python {0}".format(__version__)
